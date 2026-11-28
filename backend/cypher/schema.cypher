CREATE CONSTRAINT data_record_id IF NOT EXISTS
FOR (record:DataRecord) REQUIRE record.dataRecordId IS UNIQUE;

CREATE CONSTRAINT periodic_set_id IF NOT EXISTS
FOR (occurrence:PeriodicSet) REQUIRE occurrence.periodicSetId IS UNIQUE;

CREATE CONSTRAINT event_id IF NOT EXISTS
FOR (event:Event) REQUIRE event.eventId IS UNIQUE;

CREATE CONSTRAINT unit_key IF NOT EXISTS
FOR (unit:Unit) REQUIRE unit.unitKey IS UNIQUE;

CREATE CONSTRAINT location_key IF NOT EXISTS
FOR (location:Location) REQUIRE location.locationKey IS UNIQUE;

CREATE CONSTRAINT material_key IF NOT EXISTS
FOR (material:Material) REQUIRE material.materialKey IS UNIQUE;

CREATE CONSTRAINT related_link_id IF NOT EXISTS
FOR ()-[link:RELATED_TO]-() REQUIRE link.linkId IS UNIQUE;

CREATE INDEX data_record_date IF NOT EXISTS
FOR (record:DataRecord) ON (record.reportDate);

CREATE FULLTEXT INDEX data_record_search IF NOT EXISTS
FOR (record:DataRecord) ON EACH [record.searchText];
