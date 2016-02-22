package com.linkedin.hello.pig;

import com.linkedin.data.CountByCountryPythonJob.CountByCountryPythonJob;
import com.linkedin.hello.pig.helper.Constants;
import com.linkedin.hello.pig.helper.SeedData;
import com.linkedin.lipigunit.driver.AvroPigUnitDriver;
import java.lang.reflect.InvocationTargetException;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.apache.avro.generic.GenericRecord;
import org.apache.hadoop.fs.Path;
import org.apache.pig.impl.logicalLayer.FrontendException;
import org.testng.annotations.Test;

import static org.testng.Assert.assertTrue;
import static org.testng.Assert.fail;


/**
 * Created by zglagola on 3/11/15.
 */
public class TestCountByCountryPython extends AvroPigUnitDriver<CountByCountryPythonJob> {
  //input parameters
  private static final String _profileDataParam = "profile_data=";
  //test locales
  private static final String _enUs = "en_US";
  private static final String _enZh = "en_ZH";
  private static final String _enCr = "en_CR";

  public TestCountByCountryPython()
      throws InvocationTargetException, NoSuchMethodException, InstantiationException, IllegalAccessException,
             NoSuchFieldException {
    super("src/main/pig/count_by_country_python.pig", "total");
  }

  /*
  * Verifies that count_by_country.pig can correctly count a single record input
  * */
  @Test
  public void testSingleInput()
      throws Exception {
    //generate data
    List<GenericRecord> input = createListOf(SeedData.generateProfile(_enUs));

    //set parameters

    Path inputPath = setHDFSInput(Constants.DEFAULT_INPUT_PATH, input);
    Path outputPath = setHDFSOutputPath();
    String[] args = {_profileDataParam + inputPath, Constants.OUTPUT_DIR + outputPath};

    //execute script
    List<CountByCountryPythonJob> results = executePigScript(args);

    //make expectations
    assertTrue(results != null, "Output is null");

    CountByCountryPythonJob output = results.get(0);
    assertTrue(output.getUpperCountryCode() != null, "Found null upperCountryCode");
    assertTrue(output.getUpperCountryCode().toString().equals(_enUs.toUpperCase()),
        "Expected locale to be " + _enUs.toUpperCase() + " but got" + output.getUpperCountryCode());
    assertTrue(output.getCnt() != null, "Found null cnt");
    assertTrue(output.getCnt() == 1l, "Expected count to be 1 but got " + output.getCnt());
  }

  /*
  * Verifies that count_by_country.pig can correctly count a multiple records with the same country code
  * */
  @Test
  public void testMultipleInputSameCountryCode()
      throws Exception {
    //generate data
    List<GenericRecord> input =
        createListOf(SeedData.generateProfile(_enUs), SeedData.generateProfile(_enUs));

    //set parameters

    Path inputPath = setHDFSInput(Constants.DEFAULT_INPUT_PATH, input);
    Path outputPath = setHDFSOutputPath();
    String[] args = {_profileDataParam + inputPath, Constants.OUTPUT_DIR + outputPath};

    //execute script
    List<CountByCountryPythonJob> results = executePigScript(args);

    //make expectations
    assertTrue(results != null, "Output is null");

    CountByCountryPythonJob output = results.get(0);
    assertTrue(output.getUpperCountryCode() != null, "Found null upperCountryCode");
    assertTrue(output.getUpperCountryCode().toString().equals(_enUs.toUpperCase()),
        "Expected locale to be " + _enUs.toUpperCase() + " but got" + output.getUpperCountryCode());
    assertTrue(output.getCnt() != null, "Found null cnt");
    assertTrue(output.getCnt() == 2l, "Expected count to be 2 but got " + output.getCnt());
  }

  /*
  * Verifies that count_by_country.pig can correctly count a multiple records with different country codes
  * */
  @Test
  public void testMultipleInputMultipleCountryCodes()
      throws Exception {
    //generate data
    List<GenericRecord> input =
        createListOf(SeedData.generateProfile(_enUs), SeedData.generateProfile(_enUs),
            SeedData.generateProfile(_enCr), SeedData.generateProfile(_enZh),
            SeedData.generateProfile(_enZh), SeedData.generateProfile(_enZh),
            SeedData.generateProfile(_enZh));

    //set parameters
    Path inputPath = setHDFSInput(Constants.DEFAULT_INPUT_PATH, input);
    Path outputPath = setHDFSOutputPath();
    String[] args = {_profileDataParam + inputPath, Constants.OUTPUT_DIR + outputPath};

    //execute script
    List<CountByCountryPythonJob> results = executePigScript(args);

    //make expectations
    Set<String> locales =
        new HashSet<String>(Arrays.asList(_enUs.toUpperCase(), _enZh.toUpperCase(), _enCr.toUpperCase()));
    assertTrue(results != null, "Output is null");
    assertTrue(results.size() == 3, "Expected there to 3 records, but only found " + results.size());

    for (CountByCountryPythonJob record : results) {
      CharSequence countryCode = record.getUpperCountryCode();
      assertTrue(countryCode != null, "Found null upperCountryCode");
      assertTrue(record.getCnt() != null, "Found null cnt");
      assertTrue(locales.contains(countryCode.toString()));

      //case on count based off of locale
      if (countryCode.toString().equals(_enUs.toUpperCase())) {
        assertTrue(record.getCnt() == 2l, "Expected count to be 2 but got " + record.getCnt());
      } else if (countryCode.toString().equals(_enCr.toUpperCase())) {
        assertTrue(record.getCnt() == 1l, "Expected count to be 1 but got " + record.getCnt());
      } else if (countryCode.toString().equals(_enZh.toUpperCase())) {
        assertTrue(record.getCnt() == 4l, "Expected count to be 4 but got " + record.getCnt());
      } else {
        fail("Found a locale not in the expected list: " + countryCode.toString());
      }

      //remove locale from set so we can check for deduplication
      locales.remove(countryCode.toString());
    }
  }

  /*
  * Verify that count_by_country.pig correctly fails when the input directory has a mismatched record type
  * */
  @Test(expectedExceptions = FrontendException.class)
  public void testBadInput()
      throws Exception {
    //generate data
    List<GenericRecord> input = createListOf(SeedData.generateBadSchema());

    //set parameters
    Path inputPath = setHDFSInput(Constants.DEFAULT_INPUT_PATH, input);
    Path outputPath = setHDFSOutputPath();
    String[] args = {_profileDataParam + inputPath, Constants.OUTPUT_DIR + outputPath};

    //execute script
    executePigScript(args);
  }
}
