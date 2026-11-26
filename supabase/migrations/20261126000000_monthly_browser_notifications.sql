create table public.notification_preferences (
    user_id uuid primary key references auth.users(id) on delete cascade,
    enabled boolean not null default false,
    reminder_day smallint not null default 1 check (reminder_day between 1 and 5),
    timezone text not null default 'UTC',
    locale text not null default 'en' check (locale in ('en', 'es', 'fr', 'de')),
    last_sent_month date,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.notification_preferences enable row level security;

create policy "Users can manage their own notification preferences"
on public.notification_preferences
for all
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create table public.push_subscriptions (
    endpoint text primary key,
    user_id uuid not null references auth.users(id) on delete cascade,
    p256dh text not null,
    auth text not null,
    created_at timestamptz not null default now()
);

create index push_subscriptions_user_id_idx
on public.push_subscriptions (user_id);

alter table public.push_subscriptions enable row level security;

create policy "Users can manage their own push subscriptions"
on public.push_subscriptions
for all
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);
