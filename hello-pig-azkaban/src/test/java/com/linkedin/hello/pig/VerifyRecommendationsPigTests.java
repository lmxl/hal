package com.linkedin.hello.pig;

import java.io.File;
import java.io.IOException;
import java.io.OutputStream;
import java.lang.reflect.Method;
import java.util.Arrays;

import org.apache.avro.Schema;
import org.apache.avro.Schema.Type;
import org.apache.avro.file.DataFileWriter;
import org.apache.avro.generic.GenericData;
import org.apache.avro.generic.GenericDatumWriter;
import org.apache.avro.generic.GenericRecord;

import org.apache.commons.lang.StringUtils;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.log4j.Logger;
import org.apache.pig.pigunit.PigTest;

import org.testng.Assert;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

/**
 * Tests for verify_recommendations.pig, a sample Pig script used for data verification.
 * @author mhayes
 */
public class VerifyRecommendationsPigTests 
{ 
  private Logger _log = Logger.getLogger(VerifyRecommendationsPigTests.class);

  private Path _inputPath;
  private Path _outputPath;
  private FileSystem _fs;

  private DataFileWriter<GenericRecord> _dataWriter;
  private OutputStream _outputStream;
  private Schema _schema;

  @BeforeMethod
  public void beforeMethod(Method method)
  {
    System.setProperty("udf.import.list",
        StringUtils.join(Arrays.asList(
            "oink.",
            "com.linkedin.pig.",
            "com.linkedin.pig.date.",
            "org.apache.pig.piggybank.",
            "com.linkedin.pig.characters."),
          ":"));
    try
    {
      _log.info("*** Running " + method.getClass().getSimpleName() + "." + method.getName());

      String userDir = System.getProperty("user.dir");
      Assert.assertNotNull(userDir == null);
      _inputPath = new Path(new File(userDir, "rec_input").getAbsolutePath());
      _outputPath = new Path(new File(userDir, "rec_output").getAbsolutePath());

      _fs = FileSystem.get(new Configuration());
      _fs.delete(_inputPath, true);
      _fs.delete(_outputPath, true);
      _fs.mkdirs(_inputPath);

      _schema = Schema.createRecord("Recommendation", null, "com.linkedin.test", false);
      _schema.setFields(Arrays.asList(
          new Schema.Field("memberId", Schema.create(Type.INT), null, null),
          new Schema.Field("recs", Schema.createArray(Schema.create(Type.INT)), null, null)));

      _outputStream = _fs.create(new Path(_inputPath, "part-00000.avro"));
      GenericDatumWriter<GenericRecord> writer = new GenericDatumWriter<GenericRecord>(_schema);
      _dataWriter = new DataFileWriter<GenericRecord>(writer);
      _dataWriter.create(_schema, _outputStream);
    }
    catch (IOException e)
    {
      Assert.fail();
    }
  }

  @Test(enabled = false)
  public void verifyRecomendationPigTestPasses() throws Exception
  {
    writeInput(1,10,11,12);
    writeInput(2,13,15,17);
    writeInput(3,14,20,22);
    closeInput();

    String[] pigArgs = {
        "input=" + _inputPath,
        "output=" + _outputPath,
        "min_total_cnt=3",
        "min_bag_size=2",
        "min_valid_pct=90.0"
    };

    PigTest test = new PigTest("src/main/pig/verify_recommendations.pig", pigArgs);
    test.getAlias("data");
  }

  @Test
  public void verifyRecomendationPigTestFailsMinTotalCnt() throws Exception
  {
    // fewer than 3, so script will fail
    writeInput(1,10,11,12);
    writeInput(2,13,15,17);
    closeInput();

    String[] pigArgs = {
        "input=" + _inputPath,
        "output=" + _outputPath,
        "min_total_cnt=3",
        "min_bag_size=2",
        "min_valid_pct=90.0"
    };

    PigTest test = new PigTest("src/main/pig/verify_recommendations.pig", pigArgs);

    try
    {
      test.getAlias("data");
      Assert.fail("Expected script to fail");
    }
    catch (IOException e) { }
  }

  @Test
  public void verifyRecomendationPigTestFailsTooFewRecs() throws Exception
  {
    // not enough recommendations in enough bags
    writeInput(1,10,11,12);
    writeInput(2,13);
    writeInput(3,14);
    closeInput();

    String[] pigArgs = {
        "input=" + _inputPath,
        "output=" + _outputPath,
        "min_total_cnt=3",
        "min_bag_size=2",
        "min_valid_pct=90.0"
    };

    PigTest test = new PigTest("src/main/pig/verify_recommendations.pig", pigArgs);

    try
    {
      test.getAlias("data");
      Assert.fail("Expected script to fail");
    }
    catch (IOException e) { }
  }

  public void writeInput(Integer memberId, Integer... recs)
  {
    if (_dataWriter == null)
    {
      throw new RuntimeException("No data writer");
    }
    try {
      GenericRecord rec = new GenericData.Record(_schema);
      rec.put("memberId", memberId);
      rec.put("recs", Arrays.asList(recs));
      _dataWriter.append(rec);
    }
    catch (IOException e) {
      Assert.fail("Failed to write", e);
    }
  }

  public void closeInput() throws IOException
  {
    if (_dataWriter == null)
    {
      throw new RuntimeException("No data writer");
    }
    _dataWriter.close();
    _outputStream.close();
    _dataWriter = null;
    _outputStream = null;
  }
}