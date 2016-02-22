package com.linkedin.hello.pig.helper;

import com.linkedin.data.EndorsementsEndorseEvent.Endorsement;
import com.linkedin.data.EndorsementsEndorseEvent.EndorsementsEndorseEvent;
import com.linkedin.data.EndorsementsEndorseEvent.Entity;
import com.linkedin.data.EndorsementsEndorseEvent.EventHeader;
import com.linkedin.data.EndorsementsEndorseEvent.Guid;
import com.linkedin.data.EndorsementsEndorseEvent.IdentifiableEntity;
import com.linkedin.data.EndorsementsEndorseEvent.NamedEntity;
import com.linkedin.data.MemberAccount.MEMBER_ACCOUNT;

import com.linkedin.identity.Profile;
import com.linkedin.identity.member.Location;
import Identity.Profile_etl;

import com.linkedin.pigliunit.UselessSchema;
import java.nio.ByteBuffer;
import java.util.Arrays;
import java.util.Random;


/**
 * Created by zglagola on 3/9/15.
 */
public class SeedData {
  /*
  * Generates a minimal Profile_etl object changing the fields we care about for testing
  * @param countryCode: the country code we are setting in the member_summary
  * */
  public static Profile_etl generateProfile(String countryCode) {
    Profile_etl.Builder builder = Profile_etl.newBuilder();
    Profile.Builder profileBuilder = Profile.newBuilder();
    profileBuilder.setLocation(new Location(countryCode,"123","abc"));
    builder.setValue(profileBuilder.build());
    return builder.build();
  }

  /*
  * Generates a minimal EndorsementsEndorseEvent changing the fields we care about testing
  * */
  public static EndorsementsEndorseEvent generateEndorsementsEndorseEvent(int memberId) {
    //initialize random generator
    Random random = new Random();

    //initialize EventHeader variables and builder
    EventHeader.Builder eventBuilder = EventHeader.newBuilder();
    eventBuilder.setServer("server");
    eventBuilder.setService("service");
    eventBuilder.setGuid(new Guid());
    eventBuilder.setTime(random.nextLong());
    eventBuilder.setMemberId(memberId);

    //initialize IdentifiableEntity variables and builder
    IdentifiableEntity.Builder idEntityBuilder = IdentifiableEntity.newBuilder();
    idEntityBuilder.setId(random.nextLong());
    idEntityBuilder.setType(Entity.article);

    //initialize NamedEntity variables and builder
    NamedEntity.Builder namedEntityBuilder = NamedEntity.newBuilder();
    namedEntityBuilder.setId(random.nextLong());
    namedEntityBuilder.setName("name");
    namedEntityBuilder.setType(Entity.article);

    //initialize Endorsement variables and builder
    Endorsement.Builder endorsementBuilder = Endorsement.newBuilder();
    endorsementBuilder.setId(random.nextLong());
    endorsementBuilder.setEndorser(idEntityBuilder.build());
    endorsementBuilder.setRecipient(idEntityBuilder.build());
    endorsementBuilder.setEndorsedItem(namedEntityBuilder.build());

    //initialise EndorsementsEndorseEvent variables and build
    EndorsementsEndorseEvent.Builder builder = EndorsementsEndorseEvent.newBuilder();
    builder.setHeader(eventBuilder.build());
    builder.setLocation("location");
    builder.setModel("model");
    builder.setEndorsements(Arrays.asList(endorsementBuilder.build()));
    return builder.build();
  }

  /*
  * Generates a minimal MEMBER_ACCOUNT changing the fields we care about testing
  * */
  public static MEMBER_ACCOUNT generateMemberAccount(String countryCode, String postalCode) {
    //initialize random generator
    Random random = new Random();

    //initialize MEMBER_ACCOUNT variables and build
    MEMBER_ACCOUNT.Builder builder = MEMBER_ACCOUNT.newBuilder();
    builder.setCITY("city");
    builder.setCOBRANDGROUPID(random.nextLong());
    builder.setCPACODE("cpaCode");
    builder.setCREATEDDATE(random.nextLong());
    builder.setDEFAULTLOCALE("defaultLocale");
    builder.setDELETEDTS(random.nextLong());
    builder.setGEOPLACECODE("geoPlaceCode");
    builder.setGEOPOSTALCODE("geoPostalCode");
    builder.setGGMODITS(random.nextLong());
    builder.setGGSTATUS("gg glhf");
    builder.setGMTOFFSET(random.nextDouble());
    builder.setINDUSTRYID(random.nextLong());
    builder.setINVITERMEMBERID(random.nextLong());
    builder.setISACTIVE("isActive");
    builder.setISPURGED("isPurged");
    builder.setJOINIP("joinP");
    builder.setJOINIPV6(ByteBuffer.allocate(1));
    builder.setLATITUDEDEG(random.nextDouble());
    builder.setLINKEDINGENERATIONNUM(random.nextLong());
    builder.setLONGITUDEDEG(random.nextDouble());
    builder.setLumosDropdate(random.nextLong());
    builder.setMEMBERID(random.nextLong());
    builder.setMIGRATIONCONTROLVERSION(random.nextLong());
    builder.setMODIFIEDDATE(random.nextLong());
    builder.setREGIONCODE(random.nextLong());
    builder.setREGISTRATIONDATE(random.nextLong());
    builder.setREGISTRATIONFIRSTNAME("registrationFirstName");
    builder.setREGISTRATIONLASTNAME("registrationLastName");
    builder.setREGISTRATIONMAIDENNAME("registrationMaidenName");
    builder.setSOURCEOFTRUTH("sourceOfTruth");
    builder.setSUBSCRIBERLEVEL(random.nextLong());
    builder.setSUBSCRIBERUNTIL(random.nextLong());
    builder.setTXN(random.nextLong());
    builder.setUSERCATEGORY(random.nextLong());
    builder.setUSESDAYLIGHTSAVINGS("usesDaylightSavings");
    builder.setCOUNTRYCODE(countryCode);
    builder.setPOSTALCODE(postalCode);
    return builder.build();
  }

  /*
  * Generates a minimal UselessSchema object.
  * The intention of this object is to provide bad input for pig scripts
  * */
  public static UselessSchema generateBadSchema() {
    //initialize random generator
    Random random = new Random();

    //initialize UselessSchema variables and build
    UselessSchema.Builder builder = UselessSchema.newBuilder();
    builder.setBadName(random.nextLong());
    return builder.build();
  }
}
