-- Schema per Magazzino Scatole — da eseguire nel SQL Editor di Supabase

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  username text unique not null,
  pin_hash text not null,
  created_at timestamptz default now()
);

create table if not exists boxes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  box_number int not null,
  content text not null,
  quantity int not null default 0,
  category text,
  size text,
  location text,
  notes text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (user_id, box_number)          -- numero scatola unico per utente
);

create table if not exists login_attempts (
  username text primary key,
  failed_attempts int not null default 0,
  locked_until timestamptz,
  last_attempt_at timestamptz not null default now()
);

create index if not exists idx_boxes_user on boxes (user_id);
create index if not exists idx_login_attempts_locked_until
  on login_attempts (locked_until);

-- Vincoli idempotenti per database gia' creati.
do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.users'::regclass
      and conname = 'users_username_format'
  ) then
    alter table public.users add constraint users_username_format
      check (
        char_length(username) between 3 and 40
        and username ~ '^[a-z0-9_.-]+$'
      );
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.users'::regclass
      and conname = 'users_pin_hash_length'
  ) then
    alter table public.users add constraint users_pin_hash_length
      check (char_length(pin_hash) between 32 and 255);
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.login_attempts'::regclass
      and conname = 'login_attempts_username_format'
  ) then
    alter table public.login_attempts add constraint login_attempts_username_format
      check (
        char_length(username) between 3 and 40
        and username ~ '^[a-z0-9_.-]+$'
      );
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.login_attempts'::regclass
      and conname = 'login_attempts_failed_attempts_range'
  ) then
    alter table public.login_attempts add constraint login_attempts_failed_attempts_range
      check (failed_attempts between 0 and 100);
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.boxes'::regclass
      and conname = 'boxes_box_number_range'
  ) then
    alter table public.boxes add constraint boxes_box_number_range
      check (box_number between 1 and 9999);
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.boxes'::regclass
      and conname = 'boxes_quantity_range'
  ) then
    alter table public.boxes add constraint boxes_quantity_range
      check (quantity between 0 and 1000000);
  end if;

  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.boxes'::regclass
      and conname = 'boxes_text_lengths'
  ) then
    alter table public.boxes add constraint boxes_text_lengths
      check (
        char_length(btrim(content)) between 1 and 120
        and (category is null or char_length(category) <= 40)
        and (size is null or char_length(size) <= 80)
        and (location is null or char_length(location) <= 80)
        and (notes is null or char_length(notes) <= 500)
      );
  end if;
end $$;

create or replace function public.enforce_users_limit()
returns trigger
language plpgsql
as $$
begin
  if (select count(*) from public.users) >= 25 then
    raise exception 'user limit reached';
  end if;
  return new;
end;
$$;

drop trigger if exists trg_users_limit on public.users;
create trigger trg_users_limit
before insert on public.users
for each row execute function public.enforce_users_limit();

create or replace function public.enforce_boxes_per_user_limit()
returns trigger
language plpgsql
as $$
begin
  if (select count(*) from public.boxes where user_id = new.user_id) >= 1000 then
    raise exception 'box limit reached';
  end if;
  return new;
end;
$$;

drop trigger if exists trg_boxes_per_user_limit on public.boxes;
create trigger trg_boxes_per_user_limit
before insert on public.boxes
for each row execute function public.enforce_boxes_per_user_limit();

alter table boxes drop column if exists photo_url;

-- L'accesso avviene solo tramite l'app (chiave nei secrets del server),
-- quindi RLS resta disattivata su queste tabelle. Trade-off: con anon key
-- compromessa il DB e' leggibile/scrivibile; ruotare la key dopo il deploy.
alter table users disable row level security;
alter table boxes disable row level security;
alter table login_attempts disable row level security;

-- Foto rimosse dall'app: non creare bucket pubblici. Per installazioni
-- precedenti, il bucket inutilizzato viene reso privato se esiste.
update storage.buckets
set public = false
where id = 'box-photos';
