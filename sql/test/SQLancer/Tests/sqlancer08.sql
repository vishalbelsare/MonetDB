START TRANSACTION;
CREATE TABLE "t0" ("tc0" VARCHAR(32) NOT NULL,CONSTRAINT "t0_tc0_pkey" PRIMARY KEY ("tc0"),CONSTRAINT "t0_tc0_unique" UNIQUE ("tc0"));
INSERT INTO "t0" VALUES ('1048409847'), ('ph'), ('CV'), ('T\t'), ('!iG&');
CREATE TABLE "t1" ("tc0" VARCHAR(32) NOT NULL,CONSTRAINT "t1_tc0_unique" UNIQUE ("tc0"),CONSTRAINT "t1_tc0_fkey" FOREIGN KEY ("tc0") REFERENCES "t1" ("tc0"));
select 1 from t0 join t1 on sql_min(true, t1.tc0 between rtrim(t0.tc0) and 'a');
	-- empty
select cast("isauuid"(t1.tc0) as int) from t0 full outer join t1 on
not (sql_min(not ((interval '505207731' day) in (interval '1621733891' day)), (nullif(t0.tc0, t1.tc0)) between asymmetric (rtrim(t0.tc0)) and (cast((r'_7') in (r'', t0.tc0) as string(891)))));
ROLLBACK;

START TRANSACTION;
CREATE TABLE "sys"."t0" ("tc0" UUID NOT NULL,CONSTRAINT "t0_tc0_pkey" PRIMARY KEY ("tc0"), CONSTRAINT "t0_tc0_unique" UNIQUE ("tc0"));
COPY 8 RECORDS INTO "sys"."t0" FROM stdin USING DELIMITERS E'\t',E'\n','"';
c3fc2aee-1e03-50cf-f4c7-e6bbbb3e31a3
1efaa28b-1e44-0b5b-517b-5790d23acf5f
32cf1b57-bccb-9e00-80a2-e5af23e5cccc
5a9fe00d-b21e-6fba-efba-33ceefdebfb5
68714cba-2af2-3de1-ebd0-eba5d8da68ce
a40776ba-5e2d-02bd-1b59-0b1ad9b5d311
b5a5abcd-bb90-56a2-ffd3-f321403b6e9e
0b2d9fdb-8bfb-5fec-bebb-c658aecb013c

CREATE TABLE "sys"."t1" ("tc1" VARCHAR(486));
COPY 3 RECORDS INTO "sys"."t1" FROM stdin USING DELIMITERS E'\t',E'\n','"';
"0.9918446996922964"
NULL
"{t鏷>9縣+B"

SELECT CAST(SUM(count) AS BIGINT) FROM (SELECT ALL CAST(t0.tc0 <> ANY(VALUES (UUID 'EaFBB6AC-6Eb9-00d3-7cb0-8EC8b5ad59D8'), (UUID 'bA3ca114-Cb42-7CA8-dCdF-1fB6F2dFF704'), (UUID 'dbcea1AC-60dB-8DdA-ae8C-4FC400321eD6')) AS INT) as count FROM t0, t1) as res;
	--24
ROLLBACK;

START TRANSACTION;
CREATE TABLE "t1" ("tc0" DOUBLE NOT NULL,"tc1" CHARACTER LARGE OBJECT);
COPY 7 RECORDS INTO "sys"."t1" FROM stdin USING DELIMITERS E'\t',E'\n','"';
-1823648899	""
929994438	"0.0"
1388143804	""
-1060683114	NULL
0.6102056577219861	NULL
0.5788611308131733	NULL
0.36061345372160747	NULL

SELECT t1.tc0 FROM t1 WHERE "isauuid"(lower(lower("truncate"(t1.tc1, NULL))));
ROLLBACK;

START TRANSACTION;
CREATE TABLE "sys"."t0" ("tc0" CHARACTER LARGE OBJECT NOT NULL);
CREATE TABLE "sys"."t1" ("tc0" CHARACTER LARGE OBJECT NOT NULL);

select t0.tc0 from t0 cross join t1 where "isauuid"(cast(trim(t1.tc0) between t0.tc0 and 'a' as clob));
	-- empty
select t0.tc0 from t0 cross join t1 where "isauuid"(cast((substr(rtrim(t1.tc0, t1.tc0), abs(-32767), 0.27)) between asymmetric (t0.tc0) and (cast(time '01:09:03' as string)) as string(19)));
	-- empty
ROLLBACK;

START TRANSACTION;
CREATE TABLE "sys"."t2" ("tc0" BIGINT NOT NULL,CONSTRAINT "t2_tc0_pkey" PRIMARY KEY ("tc0"),CONSTRAINT "t2_tc0_unique" UNIQUE ("tc0"));
COPY 4 RECORDS INTO "sys"."t2" FROM stdin USING DELIMITERS E'\t',E'\n','"';
1611702516
0
-803413833
921740890

select t2.tc0, scale_down(0.87735366430185102171179778451914899051189422607421875, t2.tc0) from t2;
ROLLBACK;

START TRANSACTION;
CREATE TABLE "sys"."t0" ("tc0" BIGINT NOT NULL,CONSTRAINT "t0_tc0_pkey" PRIMARY KEY ("tc0"),CONSTRAINT "t0_tc0_unique" UNIQUE ("tc0"));
COPY 3 RECORDS INTO "sys"."t0" FROM stdin USING DELIMITERS E'\t',E'\n','"';
34818777
-2089543687
0

CREATE TABLE "sys"."t1" ("tc0" TIMESTAMP NOT NULL,CONSTRAINT "t1_tc0_pkey" PRIMARY KEY ("tc0"),CONSTRAINT "t1_tc0_unique" UNIQUE ("tc0"));
CREATE TABLE "sys"."t2" ("tc1" INTERVAL DAY  NOT NULL,CONSTRAINT "t2_tc1_pkey" PRIMARY KEY ("tc1"),CONSTRAINT "t2_tc1_unique" UNIQUE ("tc1"),CONSTRAINT "t2_tc1_unique" UNIQUE ("tc1"));
COPY 3 RECORDS INTO "sys"."t2" FROM stdin USING DELIMITERS E'\t',E'\n','"';
133611486249600.000
48909174537600.000
55100204380800.000

SELECT ALL t1.tc0 FROM t2, t1 FULL OUTER JOIN t0 ON TRUE WHERE (ascii(ltrim(replace(r'', r'l/', r'(')))) IS NOT NULL;
	-- empty
SELECT CAST(SUM(count) AS BIGINT) FROM (SELECT CAST((ascii(ltrim(replace(r'', r'l/', r'(')))) IS NOT NULL AS INT) as count FROM t2, t1 FULL OUTER JOIN t0 ON TRUE) as res;
	-- 0
ROLLBACK;

select cast('0.2.3' as decimal(10,2)); -- error, invalid decimal
select cast('+0..2' as decimal(10,2)); -- error, invalid decimal

START TRANSACTION;
create view v0(vc0) as (values (0.6686823));
create view v5(vc0) as (values ("concat"(r'-730017219', r'0.232551533113189')));

SELECT 1 FROM v0 RIGHT OUTER JOIN v5 ON 'pBU' <= ifthenelse(NOT TRUE, v5.vc0, v5.vc0);
	-- 1
SELECT CAST(SUM(count) AS BIGINT) FROM (SELECT CAST("isauuid"(splitpart(CAST(((-1206869754)|(-1610043466)) AS STRING(528)), r'0.7805510128618084', 985907011)) AS INT) as count 
FROM v0 RIGHT OUTER JOIN v5 ON ((r'pBU')<=(ifthenelse(NOT (sql_min(TRUE, TRUE)), lower(v5.vc0), "concat"(v5.vc0, v5.vc0))))) as res;
	-- 0
ROLLBACK;

START TRANSACTION;
CREATE TABLE "sys"."t2" ("tc0" TIME NOT NULL,CONSTRAINT "t2_tc0_pkey" PRIMARY KEY ("tc0"),CONSTRAINT "t2_tc0_unique" UNIQUE ("tc0"));
COPY 5 RECORDS INTO "sys"."t2" FROM stdin USING DELIMITERS E'\t',E'\n','"';
08:19:27
09:37:10
01:17:46
12:29:13
17:35:51

CREATE TABLE "sys"."t0" ("tc0" TIME NOT NULL,CONSTRAINT "t0_tc0_pkey" PRIMARY KEY ("tc0"),CONSTRAINT "t0_tc0_unique" UNIQUE ("tc0"),CONSTRAINT "t0_tc0_fkey" FOREIGN KEY ("tc0") REFERENCES "sys"."t2" ("tc0"));

create or replace view v3(vc0) as (select 'g' like '0.320466856902225');
create or replace view v4(vc0) as ((select 102) union (select cot(12.3)));
select 1 from v4, v3 where false and true > v3.vc0;
	-- empty
create or replace view v3(vc0) as ((select all ((r'g')not like("right"(case -1977591239 when -1665424052 then r'0.320466856902225' else r'' end, + (-526084344)))) where false) except 
all (select true where ((((greatest(r'', r'967262854'))ilike(upper(r'57284321'))))and(case - (-1814800471) when ((0.15968560343908733134554722710163332521915435791015625)*(87))
then "isauuid"(r'HS''HᏮCb') when least(0.2907223, 0.5006662) then ((false)or(false)) when - (0.13854998927956396759242352345609106123447418212890625) then cast(false as boolean) end))));
create or replace view v4(vc0) as ((select distinct 102 where (((("isauuid"(least(r'DT*', r'')))and(not (coalesce(false, false)))))and(not (case when 18602 then true end)))) union distinct (select cot(cast(nullif(20639, 31260) as real))));
select all t2.tc0 from v4, v3 full outer join t2 on "isauuid"(r'1870603931') cross join t0 where ((not (not ((r'\tR') is null)))and(((true)>(sql_min("isauuid"(r''), v3.vc0)))));
	-- empty
ROLLBACK;

START TRANSACTION;
CREATE TABLE "salesmart" ("city" VARCHAR(100));
INSERT INTO "salesmart" VALUES ('pT펈*1.{'),('1870507234'),('27825'),('/aF⯗u'),('10545346022400.000'),(''),('-1533465369'),(''),('29781');
create view v2(vc0, vc1) as (select all sign(((820356984)*(scale_down(0.53676551856816223651236441583023406565189361572265625, 0.5695062)))), null);
select cast(sum(count) as bigint) from (select all cast(true as int) as count from v2 join salesmart on not ((salesmart.city) between asymmetric (trim(salesmart.city, v2.vc1)) and (r'0.43353835334391844'))) as res;
	-- 5
ROLLBACK;

START TRANSACTION;
CREATE TABLE "sys"."salesmart"("city" VARCHAR(100));
COPY 5 RECORDS INTO "sys"."salesmart" FROM stdin USING DELIMITERS E'\t',E'\n','"';
"b~dEQ~"
"77378079"
"0.8200084709639743"
""
"\015"

SELECT 1 FROM salesmart WHERE CAST(1 AS BOOLEAN) OR "index"(salesmart.city, true);
	-- 5 1s
DELETE FROM salesmart WHERE (((CAST(CAST(-1073480726 AS BOOLEAN) AS BOOLEAN)) = TRUE)OR(CAST("index"(substr(salesmart.city, 1058445329, 887361238), (-528898388) IS NOT NULL) AS BOOLEAN)));
	-- Delete all rows
ROLLBACK;

PREPARE SELECT round(-'b', ?);
PREPARE SELECT sql_max(+ (0.29353363282850464), round(- (sql_min('-Infinity', ?)), ?)) LIMIT 8535194086169274474;
PREPARE VALUES (CAST(? >> 1.2 AS INTERVAL SECOND)), (interval '1' second); -- error, types decimal(2,1) and sec_interval(13,0) are not equal

START TRANSACTION;
CREATE TABLE "sys"."t2" ("tc2" INTERVAL DAY);
COPY 7 RECORDS INTO "sys"."t2" FROM stdin USING DELIMITERS E'\t',E'\n','"';
NULL
76708782777600.000
96368184086400.000
105887629728000.000
4009709779200.000
-52062825081600.000
1301584464000.000

create view v0(vc0) as (select distinct sql_neg(abs(nullif(interval '2' month, interval '3' month))) where greatest(nullif(4 in (0.42, 0.43), 'v' ilike '|pRd(Wɮ&'), ((interval '3' second) is null) = false));
MERGE INTO t2 USING (SELECT * FROM v0) AS v0 ON "isauuid"('4') WHEN MATCHED THEN UPDATE SET tc2 = INTERVAL '3' DAY;
ROLLBACK;

START TRANSACTION;
CREATE TABLE "sys"."t0" ("tc0" INTEGER NOT NULL,"tc1" TINYINT,CONSTRAINT "t0_tc0_pkey" PRIMARY KEY ("tc0"),CONSTRAINT "t0_tc0_unique" UNIQUE ("tc0"));
CREATE TABLE "sys"."t1" ("tc1" DATE);
COPY 3 RECORDS INTO "sys"."t1" FROM stdin USING DELIMITERS E'\t',E'\n','"';
1970-01-24
1970-01-24
1970-01-24
CREATE TABLE "sys"."t2" ("tc1" DATE NOT NULL,CONSTRAINT "t2_tc1_pkey" PRIMARY KEY ("tc1"));
COPY 5 RECORDS INTO "sys"."t2" FROM stdin USING DELIMITERS E'\t',E'\n','"';
1970-01-25
1970-01-14
1970-01-01
1970-01-16
1970-01-19

create view v0(vc0) as ((select least(r'KZu', trim(case interval '4' day when interval '3' day then r'8|' when interval '3' day then null end))) 
intersect distinct (select distinct nullif(ifthenelse((3) not in (2.33, 4.02, -4), r'J{⹾<PBj‣r', 
cast(case when 62 then 0.34 when 51 then 0.3 when 34 then 0.4 end as string(274))), sql_max(r'5,賓', 
cast(case 3 when 43 then 44 when 0.23 then 0.3 end as string)))));
create view v1(vc0) as ((select abs(-4)) intersect distinct (select distinct + (radians(abs(0.4))) group by 3));
create view v2(vc0) as (select cast((r'|S4 흮,8GQ') not between symmetric (r'3840') and (r'n') as int));
create view v3(vc0) as (values (cast(((abs(0.11))-(((round(0.3, 3))<<(((-3)+(5)))))) as decimal))) with check option;

SELECT CAST(SUM(count) AS BIGINT) FROM (SELECT CAST(FALSE AS INT) as count FROM t2, t1, v2 FULL OUTER JOIN t0 ON "isauuid"(r'2A') NATURAL JOIN v1 NATURAL JOIN v3) as res;
ROLLBACK;

START TRANSACTION;
create view v7(vc0, vc1) as (select all 56, replace(r'0.0074401190660642325', "insert"(r'0.9471086251830542', null, 1872651914, r'(Ga_'), r'2]vK') where not (not (false))) with check option;
select 1 from v7 where not (((cast(scale_up(4751, -1823537248) as string(86)))not like(v7.vc1)));
ROLLBACK;

START TRANSACTION;
CREATE TABLE "sys"."t1" ("tc0" BIGINT);
COPY 4 RECORDS INTO "sys"."t1" FROM stdin USING DELIMITERS E'\t',E'\n','"';
284462307
1404201729
1549521937
452608969

SELECT 1 FROM t1 WHERE ('1255780658' > (least(1287317023, ((0.8056138 + t1.tc0) ))));
SELECT CAST(SUM(count) AS BIGINT) FROM (SELECT CAST(('1255780658' > (least(1287317023, ((0.8056138 + t1.tc0))))) AS INT) as count FROM t1) as res;
ROLLBACK;

START TRANSACTION;
CREATE TABLE "sys"."t2" ("tc0" INTEGER NOT NULL);
COPY 6 RECORDS INTO "sys"."t2" FROM stdin USING DELIMITERS E'\t',E'\n','"';
604800000
29477
1
1450957756
805478917
94

select round(t2.tc0, 88) from t2;
ROLLBACK;

PREPARE (SELECT DISTINCT ((CAST(- (CASE r'' WHEN r'tU1{D^㙝U' THEN 1739172851 WHEN ? THEN -1313600539 WHEN r'X(%4}' THEN NULL WHEN r')帘''舻CD' THEN 95 END) AS BIGINT))&(least(- (-235253756), 64)))
WHERE ((rtrim(r'Z'))LIKE(r'rK'))) UNION ALL (SELECT ALL ? WHERE (scale_down(ifthenelse(TRUE, 18, ?), r'4')) IS NULL);

SELECT round(- (((-443710828)||(1616633099))), 789092170);
