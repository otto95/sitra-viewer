CREATE CONSTRAINT report_record_id IF NOT EXISTS
FOR (report:Report) REQUIRE report.recordId IS UNIQUE;

CREATE CONSTRAINT fixed_set_id IF NOT EXISTS
FOR (fixedSet:FixedSet) REQUIRE fixedSet.fixedSetId IS UNIQUE;

CREATE CONSTRAINT periodic_set_id IF NOT EXISTS
FOR (periodicSet:PeriodicSet) REQUIRE periodicSet.periodicSetId IS UNIQUE;

CREATE CONSTRAINT unit_key IF NOT EXISTS
FOR (unit:Unit) REQUIRE unit.unitKey IS UNIQUE;

CREATE CONSTRAINT source_group_key IF NOT EXISTS
FOR (sourceGroup:SourceGroup) REQUIRE sourceGroup.groupKey IS UNIQUE;

CREATE CONSTRAINT nationality_code IF NOT EXISTS
FOR (nationality:Nationality) REQUIRE nationality.code IS UNIQUE;

CREATE CONSTRAINT country_code IF NOT EXISTS
FOR (country:Country) REQUIRE country.code IS UNIQUE;

CREATE CONSTRAINT operation_type_code IF NOT EXISTS
FOR (operationType:OperationType) REQUIRE operationType.code IS UNIQUE;

CREATE CONSTRAINT province_code IF NOT EXISTS
FOR (province:Province) REQUIRE province.code IS UNIQUE;

CREATE CONSTRAINT related_link_id IF NOT EXISTS
FOR ()-[link:RELATED_TO]-() REQUIRE link.linkId IS UNIQUE;

CREATE INDEX report_message_sent_date IF NOT EXISTS
FOR (report:Report) ON (report.reportDate);

CREATE FULLTEXT INDEX report_search IF NOT EXISTS
FOR (report:Report) ON EACH [report.searchText];
