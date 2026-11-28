begin;

select plan(55);

insert into auth.users (id, email)
values
    ('11111111-1111-4111-8111-111111111111', 'rls-a@example.com'),
    ('22222222-2222-4222-8222-222222222222', 'rls-b@example.com'),
    ('33333333-3333-4333-8333-333333333333', 'rls-c@example.com');

insert into public.wishes (id, user_id, name, price_cents)
values
    (900000001, '11111111-1111-4111-8111-111111111111', 'rls-a-wish', 100),
    (900000002, '22222222-2222-4222-8222-222222222222', 'rls-b-wish', 200);

insert into public.price_history (wish_id, price_cents)
select id, 100 from public.wishes where name = 'rls-a-wish';

insert into public.price_history (wish_id, price_cents)
select id, 200 from public.wishes where name = 'rls-b-wish';

insert into public.budgets (user_id, month, amount_cents)
values
    ('11111111-1111-4111-8111-111111111111', '2099-01', 1000),
    ('22222222-2222-4222-8222-222222222222', '2099-01', 2000);

insert into public.notification_preferences (user_id)
values
    ('11111111-1111-4111-8111-111111111111'),
    ('22222222-2222-4222-8222-222222222222');

insert into public.push_subscriptions (endpoint, user_id, p256dh, auth)
values
    ('https://fcm.googleapis.com/rls-test-a', '11111111-1111-4111-8111-111111111111', 'key-a', 'auth-a'),
    ('https://fcm.googleapis.com/rls-test-b', '22222222-2222-4222-8222-222222222222', 'key-b', 'auth-b');

select ok(not has_table_privilege('anon', 'public.wishes', 'SELECT'), 'anon cannot read wishes');
select ok(not has_table_privilege('anon', 'public.price_history', 'SELECT'), 'anon cannot read price history');
select ok(not has_table_privilege('anon', 'public.budgets', 'SELECT'), 'anon cannot read budgets');
select ok(not has_table_privilege('anon', 'public.notification_preferences', 'SELECT'), 'anon cannot read notification preferences');
select ok(not has_table_privilege('anon', 'public.push_subscriptions', 'SELECT'), 'anon cannot read push subscriptions');

select ok(not has_table_privilege('anon', 'public.wishes', 'INSERT'), 'anon cannot insert wishes');
select ok(not has_table_privilege('anon', 'public.price_history', 'INSERT'), 'anon cannot insert price history');
select ok(not has_table_privilege('anon', 'public.budgets', 'INSERT'), 'anon cannot insert budgets');
select ok(not has_table_privilege('anon', 'public.notification_preferences', 'INSERT'), 'anon cannot insert notification preferences');
select ok(not has_table_privilege('anon', 'public.push_subscriptions', 'INSERT'), 'anon cannot insert push subscriptions');

select ok(not has_table_privilege('authenticated', 'public.wishes', 'TRUNCATE'), 'authenticated cannot truncate wishes');
select ok(not has_table_privilege('authenticated', 'public.price_history', 'TRUNCATE'), 'authenticated cannot truncate price history');
select ok(not has_table_privilege('authenticated', 'public.budgets', 'TRUNCATE'), 'authenticated cannot truncate budgets');
select ok(not has_table_privilege('authenticated', 'public.notification_preferences', 'TRUNCATE'), 'authenticated cannot truncate notification preferences');
select ok(not has_table_privilege('authenticated', 'public.push_subscriptions', 'TRUNCATE'), 'authenticated cannot truncate push subscriptions');

select ok((select relrowsecurity from pg_class where oid = 'public.wishes'::regclass), 'RLS is enabled for wishes');
select ok((select relrowsecurity from pg_class where oid = 'public.price_history'::regclass), 'RLS is enabled for price history');
select ok((select relrowsecurity from pg_class where oid = 'public.budgets'::regclass), 'RLS is enabled for budgets');
select ok((select relrowsecurity from pg_class where oid = 'public.notification_preferences'::regclass), 'RLS is enabled for notification preferences');
select ok((select relrowsecurity from pg_class where oid = 'public.push_subscriptions'::regclass), 'RLS is enabled for push subscriptions');

select ok(has_table_privilege('service_role', 'public.wishes', 'SELECT'), 'service_role can read wishes for reminders');
select ok(has_table_privilege('service_role', 'public.notification_preferences', 'SELECT'), 'service_role can read reminder preferences');
select ok(has_table_privilege('service_role', 'public.notification_preferences', 'UPDATE'), 'service_role can record reminder delivery');
select ok(has_table_privilege('service_role', 'public.push_subscriptions', 'SELECT'), 'service_role can read push subscriptions');
select ok(has_table_privilege('service_role', 'public.push_subscriptions', 'DELETE'), 'service_role can remove expired subscriptions');

set local role authenticated;
select set_config('request.jwt.claims', '{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated"}', true);
select set_config('request.jwt.claim.sub', '11111111-1111-4111-8111-111111111111', true);

select is((select count(*) from public.wishes where name like 'rls-%-wish'), 1::bigint, 'user A sees only their wishes');
select is((select count(*) from public.price_history), 1::bigint, 'user A sees only their price history');
select is((select count(*) from public.budgets where month = '2099-01'), 1::bigint, 'user A sees only their budgets');
select is((select count(*) from public.notification_preferences), 1::bigint, 'user A sees only their notification preferences');
select is((select count(*) from public.push_subscriptions where endpoint like 'https://fcm.googleapis.com/rls-test-%'), 1::bigint, 'user A sees only their push subscriptions');

select set_config('request.jwt.claims', '{"sub":"22222222-2222-4222-8222-222222222222","role":"authenticated"}', true);
select set_config('request.jwt.claim.sub', '22222222-2222-4222-8222-222222222222', true);

select is((select count(*) from public.wishes where name like 'rls-%-wish'), 1::bigint, 'user B sees only their wishes');
select is((select count(*) from public.price_history), 1::bigint, 'user B sees only their price history');
select is((select count(*) from public.budgets where month = '2099-01'), 1::bigint, 'user B sees only their budgets');
select is((select count(*) from public.notification_preferences), 1::bigint, 'user B sees only their notification preferences');
select is((select count(*) from public.push_subscriptions where endpoint like 'https://fcm.googleapis.com/rls-test-%'), 1::bigint, 'user B sees only their push subscriptions');

select set_config('request.jwt.claims', '{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated"}', true);
select set_config('request.jwt.claim.sub', '11111111-1111-4111-8111-111111111111', true);

select lives_ok(
    $$insert into public.wishes (user_id, name, price_cents) values (auth.uid(), 'rls-a-new-wish', 300)$$,
    'user A can insert their own wish'
);
select lives_ok(
    $$insert into public.price_history (wish_id, price_cents) select id, 300 from public.wishes where name = 'rls-a-wish'$$,
    'user A can insert price history for their own wish'
);
select lives_ok(
    $$insert into public.budgets (user_id, month, amount_cents) values (auth.uid(), '2099-02', 3000)$$,
    'user A can insert their own budget'
);
select lives_ok(
    $$update public.notification_preferences set enabled = true where user_id = auth.uid()$$,
    'user A can update their own notification preferences'
);
select lives_ok(
    $$insert into public.push_subscriptions (endpoint, user_id, p256dh, auth) values ('https://fcm.googleapis.com/rls-test-a-new', auth.uid(), 'key-a-new', 'auth-a-new')$$,
    'user A can insert their own push subscription'
);

select throws_ok(
    $$insert into public.wishes (user_id, name, price_cents) values ('22222222-2222-4222-8222-222222222222', 'rls-a-forged-wish', 300)$$,
    '42501',
    null,
    'user A cannot create a wish for user B'
);
select throws_ok(
    $$insert into public.price_history (wish_id, price_cents) values (900000002, 300)$$,
    '42501',
    null,
    'user A cannot add history to user B wish'
);
select throws_ok(
    $$insert into public.budgets (user_id, month, amount_cents) values ('22222222-2222-4222-8222-222222222222', '2099-02', 3000)$$,
    '42501',
    null,
    'user A cannot create a budget for user B'
);
select throws_ok(
    $$insert into public.notification_preferences (user_id) values ('33333333-3333-4333-8333-333333333333')$$,
    '42501',
    null,
    'user A cannot create preferences for user C'
);
select throws_ok(
    $$insert into public.push_subscriptions (endpoint, user_id, p256dh, auth) values ('https://fcm.googleapis.com/rls-test-forged', '22222222-2222-4222-8222-222222222222', 'key-forged', 'auth-forged')$$,
    '42501',
    null,
    'user A cannot create a subscription for user B'
);

select is((with changed as (update public.wishes set name = 'rls-hacked-wish' where name = 'rls-b-wish' returning 1) select count(*) from changed), 0::bigint, 'user A cannot update user B wishes');
select is((with changed as (update public.price_history set price_cents = 999 where wish_id = 900000002 returning 1) select count(*) from changed), 0::bigint, 'user A cannot update user B price history');
select is((with changed as (update public.budgets set amount_cents = 999 where user_id = '22222222-2222-4222-8222-222222222222' and month = '2099-01' returning 1) select count(*) from changed), 0::bigint, 'user A cannot update user B budgets');
select is((with changed as (update public.notification_preferences set enabled = false where user_id = '22222222-2222-4222-8222-222222222222' returning 1) select count(*) from changed), 0::bigint, 'user A cannot update user B notification preferences');
select is((with changed as (update public.push_subscriptions set auth = 'hacked' where endpoint = 'https://fcm.googleapis.com/rls-test-b' returning 1) select count(*) from changed), 0::bigint, 'user A cannot update user B push subscriptions');

select is((with changed as (delete from public.wishes where name = 'rls-b-wish' returning 1) select count(*) from changed), 0::bigint, 'user A cannot delete user B wishes');
select is((with changed as (delete from public.price_history where wish_id = 900000002 returning 1) select count(*) from changed), 0::bigint, 'user A cannot delete user B price history');
select is((with changed as (delete from public.budgets where user_id = '22222222-2222-4222-8222-222222222222' and month = '2099-01' returning 1) select count(*) from changed), 0::bigint, 'user A cannot delete user B budgets');
select is((with changed as (delete from public.notification_preferences where user_id = '22222222-2222-4222-8222-222222222222' returning 1) select count(*) from changed), 0::bigint, 'user A cannot delete user B notification preferences');
select is((with changed as (delete from public.push_subscriptions where endpoint = 'https://fcm.googleapis.com/rls-test-b' returning 1) select count(*) from changed), 0::bigint, 'user A cannot delete user B push subscriptions');

select * from finish();
rollback;
