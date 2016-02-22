package com.linkedin.hello.pig;

import com.linkedin.hello.utility.event.EventWriter;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.Calendar;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

import org.apache.commons.lang.StringUtils;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.log4j.Logger;
import org.apache.pig.data.Tuple;
import org.apache.pig.pigunit.PigTest;

import org.testng.Assert;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

/**
 * Tests for member_event_count.pig, a sample Pig script that counts events per member.
 * @author mhayes
 */
public class MemberEventCountPigTests
{
  private Logger _log = Logger.getLogger(MemberEventCountPigTests.class);

  private EventWriter _writer;
  private Path _inputPath;
  private Path _outputPath;
  private FileSystem _fs;

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
      _inputPath = new Path(new File(userDir, "pig_input").getAbsolutePath());
      _outputPath = new Path(new File(userDir, "pig_output").getAbsolutePath());

      _fs = FileSystem.get(new Configuration());
      _fs.delete(_inputPath, true);
      _fs.delete(_outputPath, true);
      _fs.mkdirs(_inputPath);

      _writer = new EventWriter(_inputPath, FileSystem.get(new Configuration()));
    }
    catch (IOException e)
    {
      Assert.fail();
    }
  }

  @Test
  public void memberEventCountPigTest() throws Exception
  {
    Calendar cal = Calendar.getInstance();

    // Start yesterday, as LiAvroStorage expects. Here's something very annoying: LiAvroStorage
    // actually has a storage.timezone parameter that is set to "America/Los_Angeles" by default,
    // but the PCX machines are set to UTC. Thus, we need to write an extra day's worth of events
    // in case PCX has rolled over to the next day but the West Coast has not.
    cal.add(Calendar.DAY_OF_MONTH, -1);
    _writer.open(cal);
    _writer.add(1,2,2,3,3,3);
    _writer.close();

    cal.add(Calendar.DAY_OF_MONTH, -1);
    _writer.open(cal);
    _writer.add(1,2,2,3,3,3);
    _writer.close();

    cal.add(Calendar.DAY_OF_MONTH, -1);
    _writer.open(cal);
    _writer.add(1,2,2,3,3,3);
    _writer.close();

    String[] pigArgs = {
        "event_path=" + _inputPath,
        "output_path=" + _outputPath,
        "num_days=2"
    };

    PigTest test = new PigTest("src/main/pig/member_event_count.pig", pigArgs);

    Map<Integer,Long> counts = new HashMap<Integer, Long>();
    Iterator<Tuple> tuples = test.getAlias("events");

    while (tuples.hasNext())
    {
      Tuple t = tuples.next();
      counts.put((Integer)t.get(0), (Long)t.get(1));
    }

    Assert.assertEquals(3, counts.size());

    Assert.assertTrue(counts.containsKey(1));
    Assert.assertEquals(2, counts.get(1).intValue());

    Assert.assertTrue(counts.containsKey(2));
    Assert.assertEquals(4, counts.get(2).intValue());

    Assert.assertTrue(counts.containsKey(3));
    Assert.assertEquals(6, counts.get(3).intValue());
  }
}