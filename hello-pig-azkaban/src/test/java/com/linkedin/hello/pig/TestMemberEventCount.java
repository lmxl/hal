package com.linkedin.hello.pig;

import com.linkedin.data.MemberEventCountJob.MemberEventCountJob;
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
 * Compare this with MemberEventCountPigTests.java to see the before and after snapshot using Avro Pig Unit
 * Shameless plug go/avropigunit
 * Created by zglagola on 3/11/15.
 */
public class TestMemberEventCount extends AvroPigUnitDriver<MemberEventCountJob> {
  //input parameters
  private static final String _eventPathParam = "event_path=";
  private static final String _numDaysParam = "num_days=";
  private static final int _singleDay = 1;
  private static final int _multipleDays = 2;

  /*
  * Constructor class to tell Avro pig unit where to find the script and what alias to intercept.
  * The current implementation specifies that the schema of the typed extension and the schema of the alias
  * in the pig script match up
  * */
  public TestMemberEventCount()
      throws InvocationTargetException, NoSuchMethodException, InstantiationException, IllegalAccessException,
             NoSuchFieldException {
    super("src/main/pig/member_event_count.pig", "events");
  }

  /*
  * Verifies that member_event_count.pig can correctly count a single record input over a single day
  * */
  @Test
  public void testSingleInputOverSingleDay()
      throws Exception {
    //generate data
    List<GenericRecord> input = createListOf(SeedData.generateEndorsementsEndorseEvent(1));

    //set parameters
    Path inputPathDaily = setHDFSDailyInput(Constants.DEFAULT_INPUT_PATH, input);
    Path outputPath = setHDFSOutputPath();
    String[] args = {_eventPathParam + inputPathDaily, Constants.OUTPUT_DIR + outputPath, _numDaysParam + _singleDay};

    //execute script
    List<MemberEventCountJob> results = executePigScript(args);

    //make expectations
    assertTrue(results != null, "Output is null");

    MemberEventCountJob record = results.get(0);
    assertTrue(record != null, "First record in output is null");
    assertTrue(record.getMemberId() != null, "memberId is null");
    assertTrue(record.getMemberId() == 1l, "Expected memberId to be 1 but got " + record.getMemberId());
    assertTrue(record.getCnt() != null, "cnt is null");
    assertTrue(record.getCnt() == 1l, "Expected cnt to be 1 but got " + record.getCnt());
  }

  /*
  * Verifies that member_event_count.pig can correctly count multiple record input with the same memberId
  * */
  @Test
  public void testMultipleInputSameMemberId()
      throws Exception {
    //generate data
    List<GenericRecord> input =
        createListOf(SeedData.generateEndorsementsEndorseEvent(1), SeedData.generateEndorsementsEndorseEvent(1));

    //set parameters
    Path inputPathDaily = setHDFSDailyInput(Constants.DEFAULT_INPUT_PATH, input, input);
    Path outputPath = setHDFSOutputPath();
    String[] args =
        {_eventPathParam + inputPathDaily, Constants.OUTPUT_DIR + outputPath, _numDaysParam + _multipleDays};

    //execute script
    List<MemberEventCountJob> results = executePigScript(args);

    //make expectations
    assertTrue(results != null, "Output is null");

    MemberEventCountJob record = results.get(0);
    assertTrue(record != null, "First record in output is null");
    assertTrue(record.getMemberId() != null, "memberId is null");
    assertTrue(record.getMemberId() == 1l, "Expected memberId to be 1 but got " + record.getMemberId());
    assertTrue(record.getCnt() != null, "cnt is null");
    assertTrue(record.getCnt() == 4l, "Expected cnt to be 4 but got " + record.getCnt());
  }

  /*
  * Verifies that member_event_count.pig can correctly count multiple record input with multiple memberIds
  * */
  @Test
  public void testMultipleInputMultipleMemberId()
      throws Exception {
    //generate data
    List<GenericRecord> inputMemberOne =
        createListOf(SeedData.generateEndorsementsEndorseEvent(1), SeedData.generateEndorsementsEndorseEvent(1));
    List<GenericRecord> inputMemberTwo =
        createListOf(SeedData.generateEndorsementsEndorseEvent(2), SeedData.generateEndorsementsEndorseEvent(2),
            SeedData.generateEndorsementsEndorseEvent(2));

    //set parameters
    Path inputPathDaily = setHDFSDailyInput(Constants.DEFAULT_INPUT_PATH, inputMemberOne, inputMemberTwo);
    Path outputPath = setHDFSOutputPath();
    String[] args =
        {_eventPathParam + inputPathDaily, Constants.OUTPUT_DIR + outputPath, _numDaysParam + _multipleDays};

    //execute script
    List<MemberEventCountJob> results = executePigScript(args);

    //make expectations
    Set<Long> expectedIntegers = new HashSet<Long>(Arrays.asList(1l, 2l));
    assertTrue(results != null, "Output is null");
    assertTrue(results.size() == 2, "Expected 2 records but found " + results.size());

    for (MemberEventCountJob record : results) {
      Long memberId = record.getMemberId();
      assertTrue(record != null, "First record in output is null");
      assertTrue(memberId != null, "memberId is null");
      assertTrue(record.getCnt() != null, "cnt is null");
      assertTrue(expectedIntegers.contains(memberId), "Found memberId not in list of expected: " + memberId);

      //case on memberId to expect count
      if (memberId == 1l) {
        assertTrue(record.getCnt() == 2l, "Expected 2 records for memberId 1 but got " + record.getCnt());
      } else if (memberId == 2l) {
        assertTrue(record.getCnt() == 3l, "Expected 3 records for memberId 2 but got " + record.getCnt());
      } else {
        fail("Found a memberId not in the expected list: " + record.getMemberId());
      }

      //remove expected integers to check for deduplication
      expectedIntegers.remove(memberId);
    }
  }

  /*
  * Verifies that member_event_count.pig fails with the correct error on a bad input schema
  * */
  @Test(expectedExceptions = FrontendException.class)
  public void testBadInput()
      throws Exception {
    //generate data
    List<GenericRecord> input = createListOf(SeedData.generateBadSchema());

    //set parameters
    Path inputPath = setHDFSDailyInput(Constants.DEFAULT_INPUT_PATH, input);
    Path outputPath = setHDFSOutputPath();
    String[] args = {_eventPathParam + inputPath, Constants.OUTPUT_DIR + outputPath, _numDaysParam + _singleDay};

    //execute script
    executePigScript(args);
  }
}
