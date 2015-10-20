# Test storing Python objects in the database using the cPickle module to convert the objects to encoded strings
START TRANSACTION;


CREATE FUNCTION pyapi21_create() returns TABLE(s STRING)
language P
{
	import cPickle
    a = 3
    b = "hello"
    c = [3, 37, "hello"]
    d = numpy.array([44, 55])
    e = numpy.ma.masked_array([1, 2, 3], [0, 1, 0])


    result = dict()
    result['s'] = [cPickle.dumps(x) for x in [a,b,c,d,e]]
    return result
};

CREATE FUNCTION pyapi21_load(objects STRING) returns BOOLEAN
LANGUAGE P
{
	import cPickle
	for x in [cPickle.loads(y) for y in objects]:
		print str(type(x)) + ": " + str(x)
	return True
};

CREATE TABLE python_objects AS SELECT * FROM pyapi21_create() WITH DATA;
SELECT pyapi21_load(s) FROM python_objects;


DROP FUNCTION pyapi21_create; DROP FUNCTION pyapi21_load; DROP TABLE python_objects;

ROLLBACK;

