-- An example of using a basic Pig script to do data
-- verification. Originally written by Matthew Hayes.

-- Here we are checking the following conditions are met:
-- 1) Recommendations generated for at least $min_total_cnt members
-- 2) At least $min_valid_pct of the recommendations have at least
--    $min_bag_size in the bag

-- In addition to this data verification script, look at the
-- PigUnit tests for this in VerifyRecommendationsPigTests.java.

DEFINE Assert datafu.pig.util.Assert();

data = LOAD '$input' USING LiAvroStorage();

data = FOREACH data GENERATE
  ((SIZE(recs) >= $min_bag_size) ? 1 : 0) as valid_size;

data = FOREACH (GROUP data ALL) GENERATE
  SIZE(data) as total_cnt,
  SUM(data.valid_size) as valid_bag_cnt;

data = FOREACH data GENERATE
  *,
  100.0*((double)valid_bag_cnt)/total_cnt as valid_pct;

data = FILTER data BY Assert((total_cnt >= $min_total_cnt ? 1 : 0),
                            'Fewer than $min_total_cnt recommendations');

data = FILTER data BY Assert((valid_pct >= $min_valid_pct ? 1 : 0),
                             'Fewer than $min_valid_pct% of recommendations valid');

STORE data INTO '$output' USING LiAvroStorage();