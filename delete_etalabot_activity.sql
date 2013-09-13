create index idx_activity_user_id on activity (user_id);
create index idx_activity_detail_activity_id on activity_detail (activity_id);

delete from activity_detail where activity_id in (select id from activity where user_id in (select id from "user" where name = 'etalabot'));
delete from activity where user_id in (select id from "user" where name = 'etalabot');

drop index idx_activity_user_id;
drop index idx_activity_detail_activity_id;

