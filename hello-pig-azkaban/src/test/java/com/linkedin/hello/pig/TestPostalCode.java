package com.linkedin.hello.pig;

import com.linkedin.data.CountByCountryJob.CountByCountryJob;
import com.linkedin.data.PostalCodeJob.PostalCodeJob;
import com.linkedin.hello.pig.helper.Constants;
import com.linkedin.hello.pig.helper.SeedData;
import com.linkedin.lipigunit.driver.AvroPigUnitDriver;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Random;
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
public class TestPostalCode extends AvroPigUnitDriver<PostalCodeJob> {
  private static final String _memberAccountParam = "member_account=";
  private static final String _usCountryCode = "us";
  private static final String _nonUsCountryCode = "not us";
  private static final String _defaultPostalOne = "90210";
  private static final String _defaultPostalTwo = "21769";
  private static final int _resultLimit = 10;
  private static final int _overResultLimit = 15;

  /*
  * Constructor class to tell Avro pig unit where to find the script and what alias to intercept.
  * The current implementation specifies that the schema of the typed extension and the schema of the alias
  * in the pig script match up
  * */
  public TestPostalCode()
      throws InvocationTargetException, NoSuchMethodException, InstantiationException, IllegalAccessException,
             NoSuchFieldException {
    super("src/main/pig/postal_code.pig", "top_10_postal_code");
  }

  /*
  * Verifies that postal_code.pig obeys its SLAs for filtering based on country code and postal code
  * Current SLA: country code = 'us' and postal code not null
  * */
  @Test
  public void testLocaleAndPostalCodeFilter()
      throws Exception {
    //generate data
    List<GenericRecord> input = createListOf(SeedData.generateMemberAccount(_usCountryCode, _defaultPostalOne),
        SeedData.generateMemberAccount(_nonUsCountryCode, _defaultPostalOne),
        SeedData.generateMemberAccount(_usCountryCode, null));

    //set parameters
    Path inputPath = setHDFSInput(Constants.DEFAULT_INPUT_PATH, input);
    Path outputPath = setHDFSOutputPath();
    String[] args = {_memberAccountParam + inputPath, Constants.OUTPUT_DIR + outputPath};

    //execute script
    List<PostalCodeJob> results = executePigScript(args);

    //make expectations
    assertTrue(results != null, "Output is null");
    assertTrue(results.size() == 1, "Expected only one record but found " + results.size());
    PostalCodeJob record = results.get(0);
    assertTrue(record.getPostalCode() != null, "Null postal code in record");
    assertTrue(record.getCount() != null, "Null count in record");
    assertTrue(record.getPostalCode().toString().equals(_defaultPostalOne),
        "Expected " + _defaultPostalOne + " as postal code, but got " + record.getPostalCode());
    assertTrue(record.getCount() == 1l, "Expect 1 record but found " + record.getCount());
  }

  /*
  * Verifies that postal_code.pig properly groups the resultant postal codes
  * */
  @Test
  public void testPostalCodeGrouping()
      throws Exception {
    //generate data
    List<GenericRecord> input = createListOf(SeedData.generateMemberAccount(_usCountryCode, _defaultPostalOne),
        SeedData.generateMemberAccount(_usCountryCode, _defaultPostalTwo),
        SeedData.generateMemberAccount(_usCountryCode, _defaultPostalTwo));

    //set parameters
    Path inputPath = setHDFSInput(Constants.DEFAULT_INPUT_PATH, input);
    Path outputPath = setHDFSOutputPath();
    String[] args = {_memberAccountParam + inputPath, Constants.OUTPUT_DIR + outputPath};

    //execute script
    List<PostalCodeJob> results = executePigScript(args);

    //make expectations
    Set<String> expectedPostalCodes = new HashSet<String>(Arrays.asList(_defaultPostalOne, _defaultPostalTwo));
    assertTrue(results != null, "Output is null");
    assertTrue(results.size() == 2, "Expected 2 records but found " + results.size());

    for (PostalCodeJob record : results) {
      assertTrue(record != null, "Null record in results");
      CharSequence postalCode = record.getPostalCode();
      assertTrue(postalCode != null, "Null postal code in record");
      assertTrue(record.getCount() != null, "Null count in record");
      assertTrue(expectedPostalCodes.contains(postalCode.toString()));

      if (postalCode.toString().equals(_defaultPostalOne)) {
        assertTrue(record.getCount() == 1l, "Expected count to be 1 but found " + record.getCount());
      } else if (postalCode.toString().equals(_defaultPostalTwo)) {
        assertTrue(record.getCount() == 2l, "Expected count to be 2 but found " + record.getCount());
      } else {
        fail("Found a postal code not in the expected list: " + postalCode.toString());
      }

      //remove anyfound postal codes to check for deduplication
      expectedPostalCodes.remove(postalCode.toString());
    }
  }

  /*
  * Verifies that postal_code.pig properly limits the number of responses
  * Current limit is 10
  * */
  @Test
  public void testResultsLimit()
      throws Exception {
    //generate data
    Random random = new Random();
    List<GenericRecord> input = new ArrayList<GenericRecord>();

    for (int i = 0; i < _overResultLimit; i++) {
      input.add(SeedData.generateMemberAccount(_usCountryCode, new BigInteger(16, random).toString()));
    }

    //set parameters
    Path inputPath = setHDFSInput(Constants.DEFAULT_INPUT_PATH, input);
    Path outputPath = setHDFSOutputPath();
    String[] args = {_memberAccountParam + inputPath, Constants.OUTPUT_DIR + outputPath};

    //execute script
    List<PostalCodeJob> results = executePigScript(args);

    //make expectations
    assertTrue(results != null, "No results");
    assertTrue(results.size() == _resultLimit, "Expected size to be " + _resultLimit + " but got " + results.size());
  }

  /*
  * Verifies that postal_code.pig fails on bad input
  * */
  @Test(expectedExceptions = FrontendException.class)
  public void testBadInput()
      throws Exception {
    //generate data
    List<GenericRecord> input = createListOf(SeedData.generateBadSchema());

    //set parameters
    Path inputPath = setHDFSInput(Constants.DEFAULT_INPUT_PATH, input);
    Path outputPath = setHDFSOutputPath();
    String[] args = {_memberAccountParam + inputPath, Constants.OUTPUT_DIR + outputPath};

    //execute script
    executePigScript(args);
  }
}
