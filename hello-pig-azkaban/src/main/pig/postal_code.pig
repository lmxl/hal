-- A canonical example of a Pig script. Finds the top 10 postal codes for members in the US.

-- You can use the Azkaban DSL to configure Pig $variables
member_account = LOAD '$member_account' using LiAvroStorage();

member_account_filtered = FILTER member_account BY COUNTRY_CODE == 'us' AND POSTAL_CODE IS NOT null;
member_account_thin = FOREACH member_account_filtered GENERATE POSTAL_CODE AS postal_code;
member_account_group = GROUP member_account_thin BY postal_code;

postal_code_count = FOREACH member_account_group GENERATE group AS postal_code, COUNT(member_account_thin) AS count;
postal_code_count_order = ORDER postal_code_count BY count desc;
top_10_postal_code = LIMIT postal_code_count_order 10;

RMF $output_path;
STORE top_10_postal_code into '$output_path' using PigStorage();
