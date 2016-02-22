-- Example Pig script showing how to use a Python UDF. This script capitalizes the
-- countryCode using a Python UDF.

REGISTER 'src/main/python/capitalize.py' using jython as myudfs;
SET default_parallel 1;

-- You can use the Azkaban DSL to configure Pig $variables
profile = LOAD '$profile_data' USING LiAvroStorage();
members = FOREACH profile GENERATE myudfs.capitalize(value.location.countryCode) AS upperCountryCode;

grp_members = GROUP members BY upperCountryCode;
total = FOREACH grp_members GENERATE group AS upperCountryCode, COUNT(members) AS cnt;

RMF $output_path
STORE total INTO '$output_path' USING LiAvroStorage();
