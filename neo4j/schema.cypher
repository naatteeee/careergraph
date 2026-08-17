// AI Job Advisor — Neo4j schema
// Apply with: cypher-shell -u neo4j -p <password> -f neo4j/schema.cypher
// (or paste into Neo4j Browser). Idempotent: safe to re-run.

// ---------------------------------------------------------------------------
// Graph model
// ---------------------------------------------------------------------------
// Nodes:
//   (:User    {user_id, profile_type, location})
//   (:Skill   {name, esco_uri})
//   (:Job     {content_hash, title, source, location, is_student_friendly, url})
//   (:Company {name, website})
//   (:Industry{name, nace_code})
//
// Relationships:
//   (:User)-[:HAS_SKILL]->(:Skill)
//   (:Job)-[:REQUIRES_SKILL {requirement}]->(:Skill)
//   (:Company)-[:OFFERS_JOB]->(:Job)
//   (:User)-[:INTERESTED_IN]->(:Industry)
//   (:Company)-[:IN_INDUSTRY]->(:Industry)
//   (:Skill)-[:RELATED_TO]-(:Skill)        // transferable / ESCO-related skills

// ---------------------------------------------------------------------------
// Uniqueness constraints (also create backing indexes)
// ---------------------------------------------------------------------------
CREATE CONSTRAINT user_id      IF NOT EXISTS FOR (u:User)     REQUIRE u.user_id IS UNIQUE;
CREATE CONSTRAINT job_hash     IF NOT EXISTS FOR (j:Job)      REQUIRE j.content_hash IS UNIQUE;
CREATE CONSTRAINT skill_name   IF NOT EXISTS FOR (s:Skill)    REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company)  REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT industry_nm  IF NOT EXISTS FOR (i:Industry) REQUIRE i.name IS UNIQUE;

// Secondary lookup indexes
CREATE INDEX job_source   IF NOT EXISTS FOR (j:Job)   ON (j.source);
CREATE INDEX job_location IF NOT EXISTS FOR (j:Job)   ON (j.location);

// ---------------------------------------------------------------------------
// Example: graph-based recommendation query (jobs ranked by shared skills,
// including transferable skills one hop away via RELATED_TO).
// ---------------------------------------------------------------------------
// MATCH (u:User {user_id: $user_id})-[:HAS_SKILL]->(us:Skill)
// OPTIONAL MATCH (us)-[:RELATED_TO]-(rel:Skill)
// WITH u, collect(DISTINCT us) + collect(DISTINCT rel) AS userSkills
// MATCH (j:Job)-[:REQUIRES_SKILL]->(req:Skill) WHERE req IN userSkills
// WITH j, count(DISTINCT req) AS overlap
// MATCH (j)-[:REQUIRES_SKILL]->(all:Skill)
// RETURN j.title, overlap, count(DISTINCT all) AS required,
//        toFloat(overlap)/count(DISTINCT all) AS coverage
// ORDER BY coverage DESC LIMIT 10;
