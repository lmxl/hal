-- This example counts PageViewEvents per member. This example shows
-- how to use PigUnit for unit tests. The PigUnit tests are in
-- MemberEventCountPigTests.java. Originally written by Matthew Hayes.

events = LOAD '$event_path' USING LiAvroStorage('date.range','num.days=$num_days');

events = FOREACH events GENERATE header.memberId as memberId;

events = FOREACH (GROUP events BY memberId)
         GENERATE group as memberId, SIZE(events) as cnt;

RMF $output_path
STORE events INTO '$output_path' USING LiAvroStorage();
