start transaction;
create table dummy4("key" varchar(32), val int);
insert into dummy4 values('AAAAAAAA',1),('BBBBBBBBB',2);
create table dummy5("key" varchar(32), val int);
insert into dummy5 values('CCCCCCCC',3),('DDDDDDDD',4);
create table dummy6 as select "key", dummy4.val as "val4", dummy5.val as "val5" from dummy4 full outer join dummy5 using ("key");

select t.name as "table_name", c.name as "column_name", c.type, c.type_digits 
from sys.tables t join sys.columns c on c.table_id = t.id where t.name = 'dummy6';

rollback;
