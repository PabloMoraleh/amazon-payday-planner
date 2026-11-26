alter default privileges for role postgres in schema public
revoke all on tables from anon, authenticated, service_role;

alter default privileges for role postgres in schema public
revoke all on sequences from anon, authenticated, service_role;

revoke all on table
    public.wishes,
    public.price_history,
    public.budgets,
    public.notification_preferences,
    public.push_subscriptions
from anon, authenticated, service_role;

grant select, insert, update, delete on table
    public.wishes,
    public.price_history,
    public.budgets,
    public.notification_preferences,
    public.push_subscriptions
to authenticated;

grant select on table public.wishes to service_role;
grant select, update on table public.notification_preferences to service_role;
grant select, delete on table public.push_subscriptions to service_role;

revoke all on sequence
    public.wishes_id_seq,
    public.price_history_id_seq,
    public.budgets_id_seq
from anon, authenticated, service_role;

grant usage, select on sequence
    public.wishes_id_seq,
    public.price_history_id_seq,
    public.budgets_id_seq
to authenticated;
