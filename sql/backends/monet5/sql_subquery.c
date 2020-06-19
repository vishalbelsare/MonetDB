/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0.  If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * Copyright 1997 - July 2008 CWI, August 2008 - 2020 MonetDB B.V.
 */

#include "monetdb_config.h"
#include "sql_subquery.h"

str
zero_or_one_error(ptr ret, const bat *bid, const bit *err)
{
	BAT *b;
	BUN c;
	size_t _s;
	const void *p;

	if ((b = BATdescriptor(*bid)) == NULL) {
		throw(SQL, "sql.zero_or_one", SQLSTATE(HY005) "Cannot access column descriptor");
	}
	c = BATcount(b);
	if (c == 0) {
		p = ATOMnilptr(b->ttype);
	} else if (c == 1 || (c > 1 && *err == false)) {
		BATiter bi = bat_iterator(b);
		p = BUNtail(bi, 0);
	} else {
		p = NULL;
		BBPunfix(b->batCacheid);
		throw(SQL, "sql.zero_or_one", SQLSTATE(21000) "Cardinality violation, scalar value expected");
	}
	_s = ATOMsize(ATOMtype(b->ttype));
	if (b->ttype == TYPE_void)
		p = &oid_nil;
	if (ATOMextern(b->ttype)) {
		_s = ATOMlen(ATOMtype(b->ttype), p);
		*(ptr *) ret = GDKmalloc(_s);
		if (*(ptr *) ret == NULL) {
			BBPunfix(b->batCacheid);
			throw(SQL, "sql.zero_or_one", SQLSTATE(HY013) MAL_MALLOC_FAIL);
		}
		memcpy(*(ptr *) ret, p, _s);
	} else if (b->ttype == TYPE_bat) {
		bat bid = *(bat *) p;
		if ((*(BAT **) ret = BATdescriptor(bid)) == NULL){
			BBPunfix(b->batCacheid);
			throw(SQL, "sql.zero_or_one", SQLSTATE(HY005) "Cannot access column descriptor");
		}
	} else if (_s == 4) {
		*(int *) ret = *(int *) p;
	} else if (_s == 1) {
		*(bte *) ret = *(bte *) p;
	} else if (_s == 2) {
		*(sht *) ret = *(sht *) p;
	} else if (_s == 8) {
		*(lng *) ret = *(lng *) p;
#ifdef HAVE_HGE
	} else if (_s == 16) {
		*(hge *) ret = *(hge *) p;
#endif
	} else {
		memcpy(ret, p, _s);
	}
	BBPunfix(b->batCacheid);
	return MAL_SUCCEED;
}

str
zero_or_one_error_bat(ptr ret, const bat *bid, const bat *err)
{
	bit t = FALSE;
	(void)err;
	return zero_or_one_error(ret, bid, &t);
}

str
zero_or_one(ptr ret, const bat *bid)
{
	bit t = TRUE;
	return zero_or_one_error(ret, bid, &t);
}

str
SQLsubzero_or_one(bat *ret, const bat *bid, const bat *gid, const bat *eid, bit *no_nil)
{
	gdk_return r;
	BAT *ng = NULL, *h = NULL, *g, *b;

	(void)no_nil;
	(void)eid;

	g = gid ? BATdescriptor(*gid) : NULL;
	if (g == NULL) {
		if (g)
			BBPunfix(g->batCacheid);
		throw(MAL, "sql.subzero_or_one", SQLSTATE(HY002) RUNTIME_OBJECT_MISSING);
	}

	if ((r = BATgroup(&ng, NULL, &h, g, NULL, NULL, NULL, NULL)) == GDK_SUCCEED) {
		lng max = 0;

		if (ng)
			BBPunfix(ng->batCacheid);
		BATmax(h, &max);
		BBPunfix(h->batCacheid);
		if (max != lng_nil && max > 1)
			throw(SQL, "sql.subzero_or_one", SQLSTATE(M0M29) "zero_or_one: cardinality violation, scalar expression expected");
	}
	BBPunfix(g->batCacheid);
	if (r == GDK_SUCCEED) {
		b = bid ? BATdescriptor(*bid) : NULL;
		BBPkeepref(*ret = b->batCacheid);
	}
	return MAL_SUCCEED;
}

#define SQLall_imp(TPE) \
	do {		\
		TPE *restrict bp = (TPE*)Tloc(b, 0), val = TPE##_nil;	\
		for (; q < c; q++) { /* find first non nil */ \
			val = bp[q]; \
			if (!is_##TPE##_nil(val)) \
				break; \
		} \
		for (; q < c; q++) { \
			TPE pp = bp[q]; \
			if (val != pp && !is_##TPE##_nil(pp)) { /* values != and not nil */ \
				val = TPE##_nil; \
				break; \
			} \
		} \
		p = &val; \
	} while (0)

str
SQLall(ptr ret, const bat *bid)
{
	BAT *b;
	BUN c, q = 0, _s;
	const void *p = NULL;

	if ((b = BATdescriptor(*bid)) == NULL) {
		throw(SQL, "sql.all", SQLSTATE(HY005) "Cannot access column descriptor");
	}
	c = BATcount(b);
	if (c == 0) {
		p = ATOMnilptr(b->ttype);
	} else if (c == 1 || (b->tsorted && b->trevsorted)) {
		p = BUNtail(bat_iterator(b), 0);
	} else if (b->ttype == TYPE_void && is_oid_nil(b->tseqbase)) {
		p = ATOMnilptr(b->ttype);
	} else {
		switch (b->ttype) {
		case TYPE_bit:
			SQLall_imp(bit);
			break;
		case TYPE_bte:
			SQLall_imp(bte);
			break;
		case TYPE_sht:
			SQLall_imp(sht);
			break;
		case TYPE_int:
			SQLall_imp(int);
			break;
		case TYPE_lng:
			SQLall_imp(lng);
			break;
#ifdef HAVE_HGE
		case TYPE_hge:
			SQLall_imp(hge);
			break;
#endif
		case TYPE_flt:
			SQLall_imp(flt);
			break;
		case TYPE_dbl:
			SQLall_imp(dbl);
			break;
		default: {
			int (*ocmp) (const void *, const void *) = ATOMcompare(b->ttype);
			const void *restrict n = ATOMnilptr(b->ttype);
			BATiter bi = bat_iterator(b);
			p = n;

			for (; q < c; q++) { /* find first non nil */
				p = BUNtail(bi, q);
				if (ocmp(n, p) != 0)
					break;
			}
			for (; q < c; q++) {
				const void *pp = BUNtail(bi, q);
				if (ocmp(p, pp) != 0 && ocmp(n, pp) != 0) { /*  values != and not nil */ 
					p = n;
					break;
				}
			}
		}
		}
	}
	_s = ATOMsize(ATOMtype(b->ttype));
	if (b->ttype == TYPE_void)
		p = &oid_nil;
	if (ATOMextern(b->ttype)) {
		_s = ATOMlen(ATOMtype(b->ttype), p);
		*(ptr *) ret = GDKmalloc(_s);
		if (*(ptr *) ret == NULL) {
			BBPunfix(b->batCacheid);
			throw(SQL, "sql.all", SQLSTATE(HY013) MAL_MALLOC_FAIL);
		}
		memcpy(*(ptr *) ret, p, _s);
	} else if (b->ttype == TYPE_bat) {
		bat bid = *(bat *) p;
		if ((*(BAT **) ret = BATdescriptor(bid)) == NULL) {
			BBPunfix(b->batCacheid);
			throw(SQL, "sql.all", SQLSTATE(HY005) "Cannot access column descriptor");
		}
	} else if (_s == 4) {
		*(int *) ret = *(int *) p;
	} else if (_s == 1) {
		*(bte *) ret = *(bte *) p;
	} else if (_s == 2) {
		*(sht *) ret = *(sht *) p;
	} else if (_s == 8) {
		*(lng *) ret = *(lng *) p;
#ifdef HAVE_HGE
	} else if (_s == 16) {
		*(hge *) ret = *(hge *) p;
#endif
	} else {
		memcpy(ret, p, _s);
	}
	BBPunfix(b->batCacheid);
	return MAL_SUCCEED;
}

#define SQLall_grp_imp(TYPE)	\
	do {			\
		const TYPE *restrict vals = (const TYPE *) Tloc(l, 0); \
		TYPE *restrict rp = (TYPE *) Tloc(res, 0); \
		while (ncand > 0) {					\
			ncand--;					\
			i = canditer_next(&ci) - l->hseqbase;		\
			if (gids == NULL ||				\
			    (gids[i] >= min && gids[i] <= max)) {	\
				if (gids)				\
					gid = gids[i] - min;		\
				else					\
					gid = (oid) i;			\
				if (oids[gid] != (BUN_NONE - 1)) { \
					if (oids[gid] == BUN_NONE) { \
						if (!is_##TYPE##_nil(vals[i])) \
							oids[gid] = i; \
					} else { \
						if (vals[oids[gid]] != vals[i] && !is_##TYPE##_nil(vals[i])) \
							oids[gid] = BUN_NONE - 1; \
					} \
				} \
			} \
		} \
		for (i = 0; i < ngrp; i++) { /* convert the found oids in values */ \
			BUN noid = oids[i]; \
			if (noid >= (BUN_NONE - 1)) { \
				rp[i] = TYPE##_nil; \
				hasnil = 1; \
			} else { \
				rp[i] = vals[noid]; \
			} \
		} \
	} while (0)

str
SQLall_grp(Client cntxt, MalBlkPtr mb, MalStkPtr stk, InstrPtr pci)
{
	bat *ret = getArgReference_bat(stk, pci, 0);
	bat *lp = getArgReference_bat(stk, pci, 1);
	bat *gp = getArgReference_bat(stk, pci, 2);
	bat *gpe = getArgReference_bat(stk, pci, 3);
	bat *sp = pci->argc == 6 ? getArgReference_bat(stk, pci, 4) : NULL;
	//bit *no_nil = getArgReference_bit(stk, pci, pci->argc == 6 ? 5 : 4); no_nil argument is ignored
	BAT *l = NULL, *g = NULL, *e = NULL, *s = NULL, *res = NULL;
	const oid *restrict gids;
	oid gid, min, max, *restrict oids = NULL; /* The oids variable controls if we have found a nil in the group so far */
	BUN i, ngrp, ncand;
	bit hasnil = 0;
	struct canditer ci;
	str msg = MAL_SUCCEED;

	(void)cntxt;
	(void)mb;
	if ((l = BATdescriptor(*lp)) == NULL) {
		msg = createException(SQL, "sql.all =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((g = BATdescriptor(*gp)) == NULL) {
		msg = createException(SQL, "sql.all =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((e = BATdescriptor(*gpe)) == NULL) {
		msg = createException(SQL, "sql.all =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if (sp && (s = BATdescriptor(*sp)) == NULL) {
		msg = createException(SQL, "sql.all =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}

	if ((msg = (str)BATgroupaggrinit(l, g, e, s, &min, &max, &ngrp, &ci, &ncand)) != NULL)
		goto bailout;
	if (g == NULL) {
		msg = createException(SQL, "sql.all =", SQLSTATE(HY005) "l and g must be aligned");
		goto bailout;
	}
	if (BATcount(l) == 0 || ngrp == 0) {
		const void *nilp = ATOMnilptr(l->ttype);
		if ((res = BATconstant(ngrp == 0 ? 0 : min, l->ttype, nilp, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "sql.all =", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
	} else {
		if ((res = COLnew(min, l->ttype, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "sql.all =", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
		if ((oids = GDKmalloc(ngrp * sizeof(oid))) == NULL) {
			msg = createException(SQL, "sql.all =", SQLSTATE(HY001) MAL_MALLOC_FAIL);
			goto bailout;
		}
		for (i = 0; i < ngrp; i++)
			oids[i] = BUN_NONE;

		if (!g || BATtdense(g))
			gids = NULL;
		else
			gids = (const oid *) Tloc(g, 0);

		switch (l->ttype) {
		case TYPE_bit:
			SQLall_grp_imp(bit);
			break;
		case TYPE_bte:
			SQLall_grp_imp(bte);
			break;
		case TYPE_sht:
			SQLall_grp_imp(sht);
			break;
		case TYPE_int:
			SQLall_grp_imp(int);
			break;
		case TYPE_lng:
			SQLall_grp_imp(lng);
			break;
#ifdef HAVE_HGE
		case TYPE_hge:
			SQLall_grp_imp(hge);
			break;
#endif
		case TYPE_flt:
			SQLall_grp_imp(flt);
			break;
		case TYPE_dbl:
			SQLall_grp_imp(dbl);
			break;
		default: {
			int (*ocmp) (const void *, const void *) = ATOMcompare(l->ttype);
			const void *restrict nilp = ATOMnilptr(l->ttype);
			BATiter li = bat_iterator(l);

			while (ncand > 0) {
				ncand--;
				i = canditer_next(&ci) - l->hseqbase;
				if (gids == NULL ||
					(gids[i] >= min && gids[i] <= max)) {
					if (gids)
						gid = gids[i] - min;
					else
						gid = (oid) i;
					if (oids[gid] != (BUN_NONE - 1)) {
						if (oids[gid] == BUN_NONE) {
							if (ocmp(BUNtail(li, i), nilp) != 0)
								oids[gid] = i;
						} else {
							const void *pi = BUNtail(li, oids[gid]);
							const void *pp = BUNtail(li, i);
							if (ocmp(pi, pp) != 0 && ocmp(pp, nilp) != 0)
								oids[gid] = BUN_NONE - 1;
						}
					}
				}
			}

			for (i = 0; i < ngrp; i++) { /* convert the found oids in values */
				BUN noid = oids[i];
				void *next;
				if (noid == BUN_NONE) {
					next = (void*) nilp;
					hasnil = 1;
				} else {
					next = BUNtail(li, noid);
				}
				if (BUNappend(res, next, false) != GDK_SUCCEED) {
					msg = createException(SQL, "sql.all =", SQLSTATE(HY001) MAL_MALLOC_FAIL);
					goto bailout;
				}
			}
		}
		}
		BATsetcount(res, ngrp);
		res->tnil = hasnil != 0;
		res->tnonil = hasnil == 0;
		res->tkey = BATcount(res) <= 1;
		res->tsorted = BATcount(res) <= 1;
		res->trevsorted = BATcount(res) <= 1;
	}

bailout:
	if (res && !msg)
		BBPkeepref(*ret = res->batCacheid);
	else if (res)
		BBPreclaim(res);
	if (l)
		BBPunfix(l->batCacheid);
	if (g)
		BBPunfix(g->batCacheid);
	if (e)
		BBPunfix(e->batCacheid);
	if (s)
		BBPunfix(s->batCacheid);
	if (oids)
		GDKfree(oids);
	return msg;
}

#define SQLnil_imp(TPE) \
	do {		\
		TPE *restrict bp = (TPE*)Tloc(b, 0);	\
		for (BUN q = 0; q < o; q++) {	\
			if (is_##TPE##_nil(bp[q])) { \
				*ret = TRUE; \
				break; \
			} \
		} \
	} while (0)

str
SQLnil(bit *ret, const bat *bid)
{
	BAT *b;

	if ((b = BATdescriptor(*bid)) == NULL) {
		throw(SQL, "sql.nil", SQLSTATE(HY005) "Cannot access column descriptor");
	}
	*ret = FALSE;
	if (BATcount(b) == 0)
		*ret = bit_nil;
	if (BATcount(b) > 0) {
		BUN o = BUNlast(b);

		switch (b->ttype) {
		case TYPE_bit:
			SQLnil_imp(bit);
			break;
		case TYPE_bte:
			SQLnil_imp(bte);
			break;
		case TYPE_sht:
			SQLnil_imp(sht);
			break;
		case TYPE_int:
			SQLnil_imp(int);
			break;
		case TYPE_lng:
			SQLnil_imp(lng);
			break;
#ifdef HAVE_HGE
		case TYPE_hge:
			SQLnil_imp(hge);
			break;
#endif
		case TYPE_flt:
			SQLnil_imp(flt);
			break;
		case TYPE_dbl:
			SQLnil_imp(dbl);
			break;
		default: {
			int (*ocmp) (const void *, const void *) = ATOMcompare(b->ttype);
			const void *restrict nilp = ATOMnilptr(b->ttype);
			BATiter bi = bat_iterator(b);

			for (BUN q = 0; q < o; q++) {
				const void *restrict c = BUNtail(bi, q);
				if (ocmp(nilp, c) == 0) {
					*ret = TRUE;
					break;
				}
			}
		}
		}
	}
	BBPunfix(b->batCacheid);
	return MAL_SUCCEED;
}

#define SQLnil_grp_imp(TYPE)	\
	do {								\
		const TYPE *restrict vals = (const TYPE *) Tloc(l, 0);		\
		while (ncand > 0) {					\
			ncand--;					\
			i = canditer_next(&ci) - l->hseqbase;		\
			if (gids == NULL ||				\
			    (gids[i] >= min && gids[i] <= max)) {	\
				if (gids)				\
					gid = gids[i] - min;		\
				else					\
					gid = (oid) i;			\
				if (ret[gid] != TRUE && is_##TYPE##_nil(vals[i])) \
					ret[gid] = TRUE; \
			} \
		} \
	} while (0)

str
SQLnil_grp(Client cntxt, MalBlkPtr mb, MalStkPtr stk, InstrPtr pci)
{
	bat *ret = getArgReference_bat(stk, pci, 0);
	bat *lp = getArgReference_bat(stk, pci, 1);
	bat *gp = getArgReference_bat(stk, pci, 2);
	bat *gpe = getArgReference_bat(stk, pci, 3);
	bat *sp = pci->argc == 6 ? getArgReference_bat(stk, pci, 4) : NULL;
	//bit *no_nil = getArgReference_bit(stk, pci, pci->argc == 6 ? 5 : 4); no_nil argument is ignored
	BAT *l = NULL, *g = NULL, *e = NULL, *s = NULL, *res = NULL;
	const oid *restrict gids;
	oid gid, min, max;
	BUN i, ngrp, ncand;
	struct canditer ci;
	str msg = MAL_SUCCEED;

	(void)cntxt;
	(void)mb;
	if ((l = BATdescriptor(*lp)) == NULL) {
		msg = createException(SQL, "sql.nil", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((g = BATdescriptor(*gp)) == NULL) {
		msg = createException(SQL, "sql.nil", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((e = BATdescriptor(*gpe)) == NULL) {
		msg = createException(SQL, "sql.nil", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if (sp && (s = BATdescriptor(*sp)) == NULL) {
		msg = createException(SQL, "sql.nil", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}

	if ((msg = (str)BATgroupaggrinit(l, g, e, s, &min, &max, &ngrp, &ci, &ncand)) != NULL)
		goto bailout;
	if (g == NULL) {
		msg = createException(SQL, "sql.nil", SQLSTATE(HY005) "l and g must be aligned");
		goto bailout;
	}
	if (BATcount(l) == 0 || ngrp == 0) {
		bit F = FALSE;
		if ((res = BATconstant(ngrp == 0 ? 0 : min, TYPE_bit, &F, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "sql.nil", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
	} else {
		bit *restrict ret;

		if ((res = COLnew(min, TYPE_bit, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "sql.nil", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
		ret = (bit *) Tloc(res, 0);
		memset(ret, FALSE, ngrp * sizeof(bit));

		if (!g || BATtdense(g))
			gids = NULL;
		else
			gids = (const oid *) Tloc(g, 0);

		switch (l->ttype) {
		case TYPE_bit:
			SQLnil_grp_imp(bit);
			break;
		case TYPE_bte:
			SQLnil_grp_imp(bte);
			break;
		case TYPE_sht:
			SQLnil_grp_imp(sht);
			break;
		case TYPE_int:
			SQLnil_grp_imp(int);
			break;
		case TYPE_lng:
			SQLnil_grp_imp(lng);
			break;
#ifdef HAVE_HGE
		case TYPE_hge:
			SQLnil_grp_imp(hge);
			break;
#endif
		case TYPE_flt:
			SQLnil_grp_imp(flt);
			break;
		case TYPE_dbl:
			SQLnil_grp_imp(dbl);
			break;
		default: {
			int (*ocmp) (const void *, const void *) = ATOMcompare(l->ttype);
			const void *nilp = ATOMnilptr(l->ttype);
			BATiter li = bat_iterator(l);

			while (ncand > 0) {
				ncand--;
				i = canditer_next(&ci) - l->hseqbase;
				if (gids == NULL ||	
					(gids[i] >= min && gids[i] <= max)) {
					if (gids)
						gid = gids[i] - min;
					else
						gid = (oid) i;
					const void *lv = BUNtail(li, i);
					if (ret[gid] != TRUE && ocmp(lv, nilp) == 0)
						ret[gid] = TRUE;
				}
			}
		}
		}
		BATsetcount(res, ngrp);
		res->tkey = BATcount(res) <= 1;
		res->tsorted = BATcount(res) <= 1;
		res->trevsorted = BATcount(res) <= 1;
		res->tnil = false;
		res->tnonil = true;
	}

bailout:
	if (res && !msg)
		BBPkeepref(*ret = res->batCacheid);
	else if (res)
		BBPreclaim(res);
	if (l)
		BBPunfix(l->batCacheid);
	if (g)
		BBPunfix(g->batCacheid);
	if (e)
		BBPunfix(e->batCacheid);
	if (s)
		BBPunfix(s->batCacheid);
	return msg;
}

str 
SQLany_cmp(bit *ret, const bit *cmp, const bit *nl, const bit *nr)
{
	*ret = FALSE;
	if (*nr == bit_nil) /* empty -> FALSE */
		*ret = FALSE;
	else if (*cmp == TRUE)
		*ret = TRUE;
	else if (*nl == TRUE || *nr == TRUE)
		*ret = bit_nil;
	return MAL_SUCCEED;
}

str 
SQLall_cmp(bit *ret, const bit *cmp, const bit *nl, const bit *nr)
{
	*ret = TRUE;
	if (*nr == bit_nil) /* empty -> TRUE */
		*ret = TRUE;
	else if (*cmp == FALSE || (*cmp == bit_nil && !*nl && !*nr))
		*ret = FALSE;
	else if (*nl == TRUE || *nr == TRUE)
		*ret = bit_nil;
	else 
		*ret = *cmp;
	return MAL_SUCCEED;
}

#define SQLanyequal_or_not_imp(TPE, OUTPUT) \
	do {							\
		TPE *rp = (TPE*)Tloc(r, 0), *lp = (TPE*)Tloc(l, 0), p = lp[0];	\
		for (BUN q = 0; q < o; q++) {	\
			TPE c = rp[q]; \
			if (is_##TPE##_nil(c)) { \
				*ret = bit_nil; \
			} else if (p == c) { \
				*ret = OUTPUT; \
				break; \
			} \
		} \
	} while (0)

str
SQLanyequal(bit *ret, const bat *bid1, const bat *bid2)
{
	BAT *l, *r;

	if ((l = BATdescriptor(*bid1)) == NULL) {
		throw(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
	}
	if ((r = BATdescriptor(*bid2)) == NULL) {
		BBPunfix(l->batCacheid);
		throw(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
	}
	*ret = FALSE;
	if (BATcount(r) > 0) {
		BUN o = BUNlast(r);

		switch (l->ttype) {
		case TYPE_bit:
			SQLanyequal_or_not_imp(bit, TRUE);
			break;
		case TYPE_bte:
			SQLanyequal_or_not_imp(bte, TRUE);
			break;
		case TYPE_sht:
			SQLanyequal_or_not_imp(sht, TRUE);
			break;
		case TYPE_int:
			SQLanyequal_or_not_imp(int, TRUE);
			break;
		case TYPE_lng:
			SQLanyequal_or_not_imp(lng, TRUE);
			break;
#ifdef HAVE_HGE
		case TYPE_hge:
			SQLanyequal_or_not_imp(hge, TRUE);
			break;
#endif
		case TYPE_flt:
			SQLanyequal_or_not_imp(flt, TRUE);
			break;
		case TYPE_dbl:
			SQLanyequal_or_not_imp(dbl, TRUE);
			break;
		default: {
			int (*ocmp) (const void *, const void *) = ATOMcompare(l->ttype);
			const void *nilp = ATOMnilptr(l->ttype);
			BATiter li = bat_iterator(l), ri = bat_iterator(r);
			const void *p = BUNtail(li, 0);

			for (BUN q = 0; q < o; q++) {
				const void *c = BUNtail(ri, q);
				if (ocmp(nilp, c) == 0)
					*ret = bit_nil;
				else if (ocmp(p, c) == 0) {
					*ret = TRUE;
					break;
				}
			}
		}
		}
	}
	BBPunfix(l->batCacheid);
	BBPunfix(r->batCacheid);
	return MAL_SUCCEED;
}

#define SQLanyequal_or_not_grp_imp(TYPE, TEST)	\
	do {								\
		const TYPE *vals1 = (const TYPE *) Tloc(l, 0);		\
		const TYPE *vals2 = (const TYPE *) Tloc(r, 0);		\
		while (ncand > 0) {					\
			ncand--;					\
			i = canditer_next(&ci) - l->hseqbase;		\
			if (gids == NULL ||				\
			    (gids[i] >= min && gids[i] <= max)) {	\
				if (gids)				\
					gid = gids[i] - min;		\
				else					\
					gid = (oid) i;			\
				if (ret[gid] != TEST) { \
					if (is_##TYPE##_nil(vals1[i]) || is_##TYPE##_nil(vals2[i])) { \
						ret[gid] = bit_nil; \
						hasnil = 1; \
					} else if (vals1[i] == vals2[i]) { \
						ret[gid] = TEST; \
					} \
				} \
			} \
		} \
	} while (0)

str
SQLanyequal_grp(Client cntxt, MalBlkPtr mb, MalStkPtr stk, InstrPtr pci)
{
	bat *ret = getArgReference_bat(stk, pci, 0);
	bat *lp = getArgReference_bat(stk, pci, 1);
	bat *rp = getArgReference_bat(stk, pci, 2);
	bat *gp = getArgReference_bat(stk, pci, 3);
	bat *gpe = getArgReference_bat(stk, pci, 4);
	bat *sp = pci->argc == 7 ? getArgReference_bat(stk, pci, 5) : NULL;
	//bit *no_nil = getArgReference_bit(stk, pci, pci->argc == 7 ? 6 : 5); no_nil argument is ignored
	BAT *l = NULL, *r = NULL, *g = NULL, *e = NULL, *s = NULL, *res = NULL;
	const oid *restrict gids;
	oid gid, min, max;
	BUN i, ngrp, ncand;
	struct canditer ci;
	str msg = MAL_SUCCEED;
	bit hasnil = 0;

	(void)cntxt;
	(void)mb;
	if ((l = BATdescriptor(*lp)) == NULL) {
		msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((r = BATdescriptor(*rp)) == NULL) {
		msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((g = BATdescriptor(*gp)) == NULL) {
		msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((e = BATdescriptor(*gpe)) == NULL) {
		msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if (sp && (s = BATdescriptor(*sp)) == NULL) {
		msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}

	if ((msg = (str)BATgroupaggrinit(l, g, e, s, &min, &max, &ngrp, &ci, &ncand)) != NULL)
		goto bailout;
	if (g == NULL) {
		msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "l, r and g must be aligned");
		goto bailout;
	}

	if (BATcount(l) == 0 || ngrp == 0) {
		bit F = FALSE;
		if ((res = BATconstant(ngrp == 0 ? 0 : min, TYPE_bit, &F, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
	} else {
		bit *restrict ret;

		if ((res = COLnew(min, TYPE_bit, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
		ret = (bit *) Tloc(res, 0);
		memset(ret, FALSE, ngrp * sizeof(bit));

		if (!g || BATtdense(g))
			gids = NULL;
		else
			gids = (const oid *) Tloc(g, 0);

		switch (l->ttype) {
		case TYPE_bit:
			SQLanyequal_or_not_grp_imp(bit, TRUE);
			break;
		case TYPE_bte:
			SQLanyequal_or_not_grp_imp(bte, TRUE);
			break;
		case TYPE_sht:
			SQLanyequal_or_not_grp_imp(sht, TRUE);
			break;
		case TYPE_int:
			SQLanyequal_or_not_grp_imp(int, TRUE);
			break;
		case TYPE_lng:
			SQLanyequal_or_not_grp_imp(lng, TRUE);
			break;
#ifdef HAVE_HGE
		case TYPE_hge:
			SQLanyequal_or_not_grp_imp(hge, TRUE);
			break;
#endif
		case TYPE_flt:
			SQLanyequal_or_not_grp_imp(flt, TRUE);
			break;
		case TYPE_dbl:
			SQLanyequal_or_not_grp_imp(dbl, TRUE);
			break;
		default: {
			int (*ocmp) (const void *, const void *) = ATOMcompare(l->ttype);
			const void *nilp = ATOMnilptr(l->ttype);
			BATiter li = bat_iterator(l), ri = bat_iterator(r);

			while (ncand > 0) {
				ncand--;
				i = canditer_next(&ci) - l->hseqbase;
				if (gids == NULL ||	
					(gids[i] >= min && gids[i] <= max)) {
					if (gids)
						gid = gids[i] - min;
					else
						gid = (oid) i;
					if (ret[gid] != TRUE) {
						const void *lv = BUNtail(li, i);
						const void *rv = BUNtail(ri, i);
						if (ocmp(lv, nilp) == 0 || ocmp(rv, nilp) == 0) {
							ret[gid] = bit_nil;
							hasnil = 1;
						} else if (ocmp(lv, rv) == 0)
							ret[gid] = TRUE;
					}
				}
			}
		}
		}
		BATsetcount(res, ngrp);
		res->tkey = BATcount(res) <= 1;
		res->tsorted = BATcount(res) <= 1;
		res->trevsorted = BATcount(res) <= 1;
		res->tnil = hasnil != 0;
		res->tnonil = hasnil == 0;
	}

bailout:
	if (res && !msg)
		BBPkeepref(*ret = res->batCacheid);
	else if (res)
		BBPreclaim(res);
	if (l)
		BBPunfix(l->batCacheid);
	if (r)
		BBPunfix(r->batCacheid);
	if (g)
		BBPunfix(g->batCacheid);
	if (e)
		BBPunfix(e->batCacheid);
	if (s)
		BBPunfix(s->batCacheid);
	return msg;
}

#define SQLanyequal_or_not_grp2_imp(TYPE, VAL1, VAL2) \
	do {								\
		const TYPE *vals1 = (const TYPE *) Tloc(l, 0);		\
		const TYPE *vals2 = (const TYPE *) Tloc(r, 0);		\
		while (ncand > 0) {					\
			ncand--;					\
			i = canditer_next(&ci) - l->hseqbase;		\
			if (gids == NULL ||				\
			    (gids[i] >= min && gids[i] <= max)) {	\
				if (gids)				\
					gid = gids[i] - min;		\
				else					\
					gid = (oid) i;			\
				if (ret[gid] != VAL1) { \
					const oid id = *(oid*)BUNtail(ii, i); \
					if (is_oid_nil(id)) { \
						ret[gid] = VAL2; \
					} else if (is_##TYPE##_nil(vals1[i]) || is_##TYPE##_nil(vals2[i])) { \
						ret[gid] = bit_nil; \
						hasnil = 1; \
					} else if (vals1[i] == vals2[i]) { \
						ret[gid] = VAL1; \
					} \
				} \
			} \
		} \
	} while (0)

str
SQLanyequal_grp2(Client cntxt, MalBlkPtr mb, MalStkPtr stk, InstrPtr pci)
{
	bat *ret = getArgReference_bat(stk, pci, 0);
	bat *lp = getArgReference_bat(stk, pci, 1);
	bat *rp = getArgReference_bat(stk, pci, 2);
	bat *ip = getArgReference_bat(stk, pci, 3);
	bat *gp = getArgReference_bat(stk, pci, 4);
	bat *gpe = getArgReference_bat(stk, pci, 5);
	bat *sp = pci->argc == 8 ? getArgReference_bat(stk, pci, 6) : NULL;
	//bit *no_nil = getArgReference_bit(stk, pci, pci->argc == 8 ? 7 : 6); no_nil argument is ignored
	BAT *l = NULL, *r = NULL, *rid = NULL, *g = NULL, *e = NULL, *s = NULL, *res = NULL;
	const oid *restrict gids;
	oid gid, min, max;
	BUN i, ngrp, ncand;
	struct canditer ci;
	str msg = MAL_SUCCEED;
	bit hasnil = 0;

	(void)cntxt;
	(void)mb;

	if ((l = BATdescriptor(*lp)) == NULL) {
		msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((r = BATdescriptor(*rp)) == NULL) {
		msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((rid = BATdescriptor(*ip)) == NULL) {
		msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((g = BATdescriptor(*gp)) == NULL) {
		msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((e = BATdescriptor(*gpe)) == NULL) {
		msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if (sp && (s = BATdescriptor(*sp)) == NULL) {
		msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}

	if ((msg = (str)BATgroupaggrinit(l, g, e, s, &min, &max, &ngrp, &ci, &ncand)) != NULL)
		goto bailout;
	if (g == NULL) {
		msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "l, r, rid and g must be aligned");
		goto bailout;
	}

	if (BATcount(l) == 0 || ngrp == 0) {
		bit F = FALSE;
		if ((res = BATconstant(ngrp == 0 ? 0 : min, TYPE_bit, &F, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
	} else {
		BATiter ii = bat_iterator(rid);
		bit *restrict ret;

		if ((res = COLnew(min, TYPE_bit, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "sql.any =", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
		ret = (bit *) Tloc(res, 0);
		memset(ret, FALSE, ngrp * sizeof(bit));

		if (!g || BATtdense(g))
			gids = NULL;
		else
			gids = (const oid *) Tloc(g, 0);

		switch (l->ttype) {
		case TYPE_bit:
			SQLanyequal_or_not_grp2_imp(bit, TRUE, FALSE);
			break;
		case TYPE_bte:
			SQLanyequal_or_not_grp2_imp(bte, TRUE, FALSE);
			break;
		case TYPE_sht:
			SQLanyequal_or_not_grp2_imp(sht, TRUE, FALSE);
			break;
		case TYPE_int:
			SQLanyequal_or_not_grp2_imp(int, TRUE, FALSE);
			break;
		case TYPE_lng:
			SQLanyequal_or_not_grp2_imp(lng, TRUE, FALSE);
			break;
#ifdef HAVE_HGE
		case TYPE_hge:
			SQLanyequal_or_not_grp2_imp(hge, TRUE, FALSE);
			break;
#endif
		case TYPE_flt:
			SQLanyequal_or_not_grp2_imp(flt, TRUE, FALSE);
			break;
		case TYPE_dbl:
			SQLanyequal_or_not_grp2_imp(dbl, TRUE, FALSE);
			break;
		default: {
			int (*ocmp) (const void *, const void *) = ATOMcompare(l->ttype);
			const void *nilp = ATOMnilptr(l->ttype);
			BATiter li = bat_iterator(l), ri = bat_iterator(r);

			while (ncand > 0) {
				ncand--;
				i = canditer_next(&ci) - l->hseqbase;
				if (gids == NULL ||
					(gids[i] >= min && gids[i] <= max)) {
					if (gids)
						gid = gids[i] - min;
					else
						gid = (oid) i;
					if (ret[gid] != TRUE) {
						const oid id = *(oid*)BUNtail(ii, i);
						if (is_oid_nil(id)) {
							ret[gid] = FALSE;
						} else {
							const void *lv = BUNtail(li, i);
							const void *rv = BUNtail(ri, i);
							if (ocmp(lv, nilp) == 0 || ocmp(rv, nilp) == 0) {
								ret[gid] = bit_nil;
								hasnil = 1;
							} else if (ocmp(lv, rv) == 0)
								ret[gid] = TRUE;
						} 
					}
				}
			}
		}
		}
		BATsetcount(res, ngrp);
		res->tkey = BATcount(res) <= 1;
		res->tsorted = BATcount(res) <= 1;
		res->trevsorted = BATcount(res) <= 1;
		res->tnil = hasnil != 0;
		res->tnonil = hasnil == 0;
	}

bailout:
	if (res && !msg)
		BBPkeepref(*ret = res->batCacheid);
	else if (res)
		BBPreclaim(res);
	if (l)
		BBPunfix(l->batCacheid);
	if (r)
		BBPunfix(r->batCacheid);
	if (rid)
		BBPunfix(rid->batCacheid);
	if (g)
		BBPunfix(g->batCacheid);
	if (e)
		BBPunfix(e->batCacheid);
	if (s)
		BBPunfix(s->batCacheid);
	return msg;
}

str
SQLallnotequal(bit *ret, const bat *bid1, const bat *bid2)
{
	BAT *l, *r;

	if ((l = BATdescriptor(*bid1)) == NULL) {
		throw(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
	}
	if ((r = BATdescriptor(*bid2)) == NULL) {
		BBPunfix(l->batCacheid);
		throw(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
	}
	*ret = TRUE;
	if (BATcount(r) > 0) {
		BUN o = BUNlast(r);

		switch (l->ttype) {
		case TYPE_bit:
			SQLanyequal_or_not_imp(bit, FALSE);
			break;
		case TYPE_bte:
			SQLanyequal_or_not_imp(bte, FALSE);
			break;
		case TYPE_sht:
			SQLanyequal_or_not_imp(sht, FALSE);
			break;
		case TYPE_int:
			SQLanyequal_or_not_imp(int, FALSE);
			break;
		case TYPE_lng:
			SQLanyequal_or_not_imp(lng, FALSE);
			break;
#ifdef HAVE_HGE
		case TYPE_hge:
			SQLanyequal_or_not_imp(hge, FALSE);
			break;
#endif
		case TYPE_flt:
			SQLanyequal_or_not_imp(flt, FALSE);
			break;
		case TYPE_dbl:
			SQLanyequal_or_not_imp(dbl, FALSE);
			break;
		default: {
			int (*ocmp) (const void *, const void *) = ATOMcompare(l->ttype);
			const void *nilp = ATOMnilptr(l->ttype);
			BATiter li = bat_iterator(l), ri = bat_iterator(r);
			const void *p = BUNtail(li, 0);

			for (BUN q = 0; q < o; q++) {
				const void *c = BUNtail(ri, q);
				if (ocmp(nilp, c) == 0)
					*ret = bit_nil;
				else if (ocmp(p, c) == 0) {
					*ret = FALSE;
					break;
				}
			}
		}
		}
	}
	BBPunfix(l->batCacheid);
	BBPunfix(r->batCacheid);
	return MAL_SUCCEED;
}

str
SQLallnotequal_grp(Client cntxt, MalBlkPtr mb, MalStkPtr stk, InstrPtr pci)
{
	bat *ret = getArgReference_bat(stk, pci, 0);
	bat *lp = getArgReference_bat(stk, pci, 1);
	bat *rp = getArgReference_bat(stk, pci, 2);
	bat *gp = getArgReference_bat(stk, pci, 3);
	bat *gpe = getArgReference_bat(stk, pci, 4);
	bat *sp = pci->argc == 7 ? getArgReference_bat(stk, pci, 5) : NULL;
	//bit *no_nil = getArgReference_bit(stk, pci, pci->argc == 7 ? 6 : 5); no_nil argument is ignored
	BAT *l = NULL, *r = NULL, *g = NULL, *e = NULL, *s = NULL, *res = NULL;
	const oid *restrict gids;
	oid gid, min, max;
	BUN i, ngrp, ncand;
	struct canditer ci;
	str msg = MAL_SUCCEED;
	bit hasnil = 0;

	(void)cntxt;
	(void)mb;
	if ((l = BATdescriptor(*lp)) == NULL) {
		msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((r = BATdescriptor(*rp)) == NULL) {
		msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((g = BATdescriptor(*gp)) == NULL) {
		msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((e = BATdescriptor(*gpe)) == NULL) {
		msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if (sp && (s = BATdescriptor(*sp)) == NULL) {
		msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}

	if ((msg = (str)BATgroupaggrinit(l, g, e, s, &min, &max, &ngrp, &ci, &ncand)) != NULL)
		goto bailout;
	if (g == NULL) {
		msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "l, r and g must be aligned");
		goto bailout;
	}

	if (BATcount(l) == 0 || ngrp == 0) {
		bit T = TRUE;
		if ((res = BATconstant(ngrp == 0 ? 0 : min, TYPE_bit, &T, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
	} else {
		bit *restrict ret;

		if ((res = COLnew(min, TYPE_bit, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
		ret = (bit *) Tloc(res, 0);
		memset(ret, TRUE, ngrp * sizeof(bit));

		if (!g || BATtdense(g))
			gids = NULL;
		else
			gids = (const oid *) Tloc(g, 0);

		switch (l->ttype) {
		case TYPE_bit:
			SQLanyequal_or_not_grp_imp(bit, FALSE);
			break;
		case TYPE_bte:
			SQLanyequal_or_not_grp_imp(bte, FALSE);
			break;
		case TYPE_sht:
			SQLanyequal_or_not_grp_imp(sht, FALSE);
			break;
		case TYPE_int:
			SQLanyequal_or_not_grp_imp(int, FALSE);
			break;
		case TYPE_lng:
			SQLanyequal_or_not_grp_imp(lng, FALSE);
			break;
#ifdef HAVE_HGE
		case TYPE_hge:
			SQLanyequal_or_not_grp_imp(hge, FALSE);
			break;
#endif
		case TYPE_flt:
			SQLanyequal_or_not_grp_imp(flt, FALSE);
			break;
		case TYPE_dbl:
			SQLanyequal_or_not_grp_imp(dbl, FALSE);
			break;
		default: {
			int (*ocmp) (const void *, const void *) = ATOMcompare(l->ttype);
			const void *nilp = ATOMnilptr(l->ttype);
			BATiter li = bat_iterator(l), ri = bat_iterator(r);

			while (ncand > 0) {
				ncand--;
				i = canditer_next(&ci) - l->hseqbase;
				if (gids == NULL ||	
					(gids[i] >= min && gids[i] <= max)) {
					if (gids)
						gid = gids[i] - min;
					else
						gid = (oid) i;
					if (ret[gid] != FALSE) {
						const void *lv = BUNtail(li, i);
						const void *rv = BUNtail(ri, i);
						if (ocmp(lv, nilp) == 0 || ocmp(rv, nilp) == 0) {
							ret[gid] = bit_nil;
							hasnil = 1;
						} else if (ocmp(lv, rv) == 0)
							ret[gid] = FALSE;
					}
				}
			}
		}
		}
		BATsetcount(res, ngrp);
		res->tkey = BATcount(res) <= 1;
		res->tsorted = BATcount(res) <= 1;
		res->trevsorted = BATcount(res) <= 1;
		res->tnil = hasnil != 0;
		res->tnonil = hasnil == 0;
	}

bailout:
	if (res && !msg)
		BBPkeepref(*ret = res->batCacheid);
	else if (res)
		BBPreclaim(res);
	if (l)
		BBPunfix(l->batCacheid);
	if (r)
		BBPunfix(r->batCacheid);
	if (g)
		BBPunfix(g->batCacheid);
	if (e)
		BBPunfix(e->batCacheid);
	if (s)
		BBPunfix(s->batCacheid);
	return msg;
}

str
SQLallnotequal_grp2(Client cntxt, MalBlkPtr mb, MalStkPtr stk, InstrPtr pci)
{
	bat *ret = getArgReference_bat(stk, pci, 0);
	bat *lp = getArgReference_bat(stk, pci, 1);
	bat *rp = getArgReference_bat(stk, pci, 2);
	bat *ip = getArgReference_bat(stk, pci, 3);
	bat *gp = getArgReference_bat(stk, pci, 4);
	bat *gpe = getArgReference_bat(stk, pci, 5);
	bat *sp = pci->argc == 8 ? getArgReference_bat(stk, pci, 6) : NULL;
	//bit *no_nil = getArgReference_bit(stk, pci, pci->argc == 8 ? 7 : 6); no_nil argument is ignored
	BAT *l = NULL, *r = NULL, *rid = NULL, *g = NULL, *e = NULL, *s = NULL, *res = NULL;
	const oid *restrict gids;
	oid gid, min, max;
	BUN i, ngrp, ncand;
	struct canditer ci;
	str msg = MAL_SUCCEED;
	bit hasnil = 0;

	(void)cntxt;
	(void)mb;

	if ((l = BATdescriptor(*lp)) == NULL) {
		msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((r = BATdescriptor(*rp)) == NULL) {
		msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((rid = BATdescriptor(*ip)) == NULL) {
		msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((g = BATdescriptor(*gp)) == NULL) {
		msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((e = BATdescriptor(*gpe)) == NULL) {
		msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if (sp && (s = BATdescriptor(*sp)) == NULL) {
		msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}

	if ((msg = (str)BATgroupaggrinit(l, g, e, s, &min, &max, &ngrp, &ci, &ncand)) != NULL)
		goto bailout;
	if (g == NULL) {
		msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "l, r, rid and g must be aligned");
		goto bailout;
	}

	if (BATcount(l) == 0 || ngrp == 0) {
		bit T = TRUE;
		if ((res = BATconstant(ngrp == 0 ? 0 : min, TYPE_bit, &T, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
	} else {
		BATiter ii = bat_iterator(rid);
		bit *restrict ret;

		if ((res = COLnew(min, TYPE_bit, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "sql.all <>", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
		ret = (bit *) Tloc(res, 0);
		memset(ret, TRUE, ngrp * sizeof(bit));

		if (!g || BATtdense(g))
			gids = NULL;
		else
			gids = (const oid *) Tloc(g, 0);

		switch (l->ttype) {
		case TYPE_bit:
			SQLanyequal_or_not_grp2_imp(bit, FALSE, TRUE);
			break;
		case TYPE_bte:
			SQLanyequal_or_not_grp2_imp(bte, FALSE, TRUE);
			break;
		case TYPE_sht:
			SQLanyequal_or_not_grp2_imp(sht, FALSE, TRUE);
			break;
		case TYPE_int:
			SQLanyequal_or_not_grp2_imp(int, FALSE, TRUE);
			break;
		case TYPE_lng:
			SQLanyequal_or_not_grp2_imp(lng, FALSE, TRUE);
			break;
#ifdef HAVE_HGE
		case TYPE_hge:
			SQLanyequal_or_not_grp2_imp(hge, FALSE, TRUE);
			break;
#endif
		case TYPE_flt:
			SQLanyequal_or_not_grp2_imp(flt, FALSE, TRUE);
			break;
		case TYPE_dbl:
			SQLanyequal_or_not_grp2_imp(dbl, FALSE, TRUE);
			break;
		default: {
			int (*ocmp) (const void *, const void *) = ATOMcompare(l->ttype);
			const void *nilp = ATOMnilptr(l->ttype);
			BATiter li = bat_iterator(l), ri = bat_iterator(r);

			while (ncand > 0) {
				ncand--;
				i = canditer_next(&ci) - l->hseqbase;
				if (gids == NULL ||
					(gids[i] >= min && gids[i] <= max)) {
					if (gids)
						gid = gids[i] - min;
					else
						gid = (oid) i;
					if (ret[gid] != FALSE) {
						const oid id = *(oid*)BUNtail(ii, i);
						if (is_oid_nil(id)) {
							ret[gid] = TRUE;
						} else {
							const void *lv = BUNtail(li, i);
							const void *rv = BUNtail(ri, i);
							if (ocmp(lv, nilp) == 0 || ocmp(rv, nilp) == 0) {
								ret[gid] = bit_nil;
								hasnil = 1;
							} else if (ocmp(lv, rv) == 0)
								ret[gid] = FALSE;
						} 
					}
				}
			}
		}
		}
		BATsetcount(res, ngrp);
		res->tkey = BATcount(res) <= 1;
		res->tsorted = BATcount(res) <= 1;
		res->trevsorted = BATcount(res) <= 1;
		res->tnil = hasnil != 0;
		res->tnonil = hasnil == 0;
	}

bailout:
	if (res && !msg)
		BBPkeepref(*ret = res->batCacheid);
	else if (res)
		BBPreclaim(res);
	if (l)
		BBPunfix(l->batCacheid);
	if (r)
		BBPunfix(r->batCacheid);
	if (rid)
		BBPunfix(rid->batCacheid);
	if (g)
		BBPunfix(g->batCacheid);
	if (e)
		BBPunfix(e->batCacheid);
	if (s)
		BBPunfix(s->batCacheid);
	return msg;
}

str
SQLexist(Client cntxt, MalBlkPtr mb, MalStkPtr stk, InstrPtr pci)
{
	BAT *b = NULL, *r = NULL;
	bit count = TRUE;

	(void)cntxt;
	if (isaBatType(getArgType(mb, pci, 1))) {
		bat *bid = getArgReference_bat(stk, pci, 1);
		if (!(b = BATdescriptor(*bid)))
			throw(SQL, "aggr.exist", SQLSTATE(HY005) "Cannot access column descriptor");
		count = BATcount(b) != 0;
	}
	if (isaBatType(getArgType(mb, pci, 0))) {
		bat *res = getArgReference_bat(stk, pci, 0);
		if ((r = BATconstant(0, TYPE_bit, &count, b ? BATcount(b) : 1, TRANSIENT)) == NULL) {
			if (b)
				BBPunfix(b->batCacheid);
			throw(SQL, "aggr.exist", SQLSTATE(HY013) MAL_MALLOC_FAIL);
		}
		BBPkeepref(*res = r->batCacheid);
	} else {
		bit *res = getArgReference_bit(stk, pci, 0);
		*res = count;
	}

	if (b)
		BBPunfix(b->batCacheid);
	return MAL_SUCCEED;
}

str
SQLsubexist(Client cntxt, MalBlkPtr mb, MalStkPtr stk, InstrPtr pci)
{
	bat *ret = getArgReference_bat(stk, pci, 0);
	bat *bp = getArgReference_bat(stk, pci, 1);
	bat *gp = getArgReference_bat(stk, pci, 2);
	bat *gpe = getArgReference_bat(stk, pci, 3);
	bat *sp = pci->argc == 6 ? getArgReference_bat(stk, pci, 4) : NULL;
	//bit *no_nil = getArgReference_bit(stk, pci, pci->argc == 6 ? 5 : 4); no_nil argument is ignored
	BAT *b = NULL, *g = NULL, *e = NULL, *s = NULL, *res = NULL;
	const oid *restrict gids;
	oid min, max;
	BUN i, ngrp, ncand;
	struct canditer ci;
	str msg = MAL_SUCCEED;

	(void)cntxt;
	(void)mb;
	if ((b = BATdescriptor(*bp)) == NULL) {
		msg = createException(SQL, "aggr.sub_exist", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((g = BATdescriptor(*gp)) == NULL) {
		msg = createException(SQL, "aggr.sub_exist", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((e = BATdescriptor(*gpe)) == NULL) {
		msg = createException(SQL, "aggr.sub_exist", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if (sp && (s = BATdescriptor(*sp)) == NULL) {
		msg = createException(SQL, "aggr.sub_exist", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}

	if ((msg = (str)BATgroupaggrinit(b, g, e, s, &min, &max, &ngrp, &ci, &ncand)) != NULL)
		goto bailout;
	if (g == NULL) {
		msg = createException(SQL, "aggr.sub_exist", SQLSTATE(HY005) "b and g must be aligned");
		goto bailout;
	}

	if (BATcount(b) == 0 || ngrp == 0) {
		bit T = FALSE;
		if ((res = BATconstant(ngrp == 0 ? 0 : min, TYPE_bit, &T, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "aggr.sub_exist", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
	} else {
		bit *restrict exists;

		if ((res = COLnew(min, TYPE_bit, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "aggr.sub_exist", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
		exists = (bit *) Tloc(res, 0);
		memset(exists, FALSE, ngrp * sizeof(bit));

		if (!g || BATtdense(g))
			gids = NULL;
		else
			gids = (const oid *) Tloc(g, 0);

		if (gids) {
			while (ncand > 0) {
				ncand--;
				i = canditer_next(&ci) - b->hseqbase;
				if (gids[i] >= min && gids[i] <= max)
					exists[gids[i] - min] = TRUE;
			}
		} else {
			while (ncand > 0) {
				ncand--;
				i = canditer_next(&ci) - b->hseqbase;
				exists[i] = TRUE;
			}
		}
		BATsetcount(res, ngrp);
		res->tkey = BATcount(res) <= 1;
		res->tsorted = BATcount(res) <= 1;
		res->trevsorted = BATcount(res) <= 1;
		res->tnil = false;
		res->tnonil = true;
	}

bailout:
	if (res && !msg)
		BBPkeepref(*ret = res->batCacheid);
	else if (res)
		BBPreclaim(res);
	if (b)
		BBPunfix(b->batCacheid);
	if (g)
		BBPunfix(g->batCacheid);
	if (e)
		BBPunfix(e->batCacheid);
	if (s)
		BBPunfix(s->batCacheid);
	return msg;
}

str
SQLnot_exist(Client cntxt, MalBlkPtr mb, MalStkPtr stk, InstrPtr pci)
{
	BAT *b = NULL, *r = NULL;
	bit count = FALSE;

	(void)cntxt;
	if (isaBatType(getArgType(mb, pci, 1))) {
		bat *bid = getArgReference_bat(stk, pci, 1);
		if (!(b = BATdescriptor(*bid)))
			throw(SQL, "aggr.not_exist", SQLSTATE(HY005) "Cannot access column descriptor");
		count = BATcount(b) == 0;
	}
	if (isaBatType(getArgType(mb, pci, 0))) {
		bat *res = getArgReference_bat(stk, pci, 0);
		if ((r = BATconstant(0, TYPE_bit, &count, b ? BATcount(b) : 1, TRANSIENT)) == NULL) {
			if (b)
				BBPunfix(b->batCacheid);
			throw(SQL, "aggr.not_exist", SQLSTATE(HY013) MAL_MALLOC_FAIL);
		}
		BBPkeepref(*res = r->batCacheid);
	} else {
		bit *res = getArgReference_bit(stk, pci, 0);
		*res = count;
	}

	if (b)
		BBPunfix(b->batCacheid);
	return MAL_SUCCEED;
}

str
SQLsubnot_exist(Client cntxt, MalBlkPtr mb, MalStkPtr stk, InstrPtr pci)
{
	bat *ret = getArgReference_bat(stk, pci, 0);
	bat *bp = getArgReference_bat(stk, pci, 1);
	bat *gp = getArgReference_bat(stk, pci, 2);
	bat *gpe = getArgReference_bat(stk, pci, 3);
	bat *sp = pci->argc == 6 ? getArgReference_bat(stk, pci, 4) : NULL;
	//bit *no_nil = getArgReference_bit(stk, pci, pci->argc == 6 ? 5 : 4); no_nil argument is ignored
	BAT *b = NULL, *g = NULL, *e = NULL, *s = NULL, *res = NULL;
	const oid *restrict gids;
	oid min, max;
	BUN i, ngrp, ncand;
	struct canditer ci;
	str msg = MAL_SUCCEED;

	(void)cntxt;
	(void)mb;
	if ((b = BATdescriptor(*bp)) == NULL) {
		msg = createException(SQL, "aggr.subnot_exist", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((g = BATdescriptor(*gp)) == NULL) {
		msg = createException(SQL, "aggr.subnot_exist", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if ((e = BATdescriptor(*gpe)) == NULL) {
		msg = createException(SQL, "aggr.subnot_exist", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}
	if (sp && (s = BATdescriptor(*sp)) == NULL) {
		msg = createException(SQL, "aggr.subnot_exist", SQLSTATE(HY005) "Cannot access column descriptor");
		goto bailout;
	}

	if ((msg = (str)BATgroupaggrinit(b, g, e, s, &min, &max, &ngrp, &ci, &ncand)) != NULL)
		goto bailout;
	if (g == NULL) {
		msg = createException(SQL, "aggr.subnot_exist", SQLSTATE(HY005) "b and g must be aligned");
		goto bailout;
	}

	if (BATcount(b) == 0 || ngrp == 0) {
		bit T = TRUE;

		if ((res = BATconstant(ngrp == 0 ? 0 : min, TYPE_bit, &T, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "aggr.subnot_exist", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
	} else {
		bit *restrict exists;

		if ((res = COLnew(min, TYPE_bit, ngrp, TRANSIENT)) == NULL) {
			msg = createException(SQL, "aggr.subnot_exist", SQLSTATE(HY005) "Cannot access column descriptor");
			goto bailout;
		}
		exists = (bit *) Tloc(res, 0);
		memset(exists, TRUE, ngrp * sizeof(bit));

		if (!g || BATtdense(g))
			gids = NULL;
		else
			gids = (const oid *) Tloc(g, 0);

		if (gids) {
			while (ncand > 0) {
				ncand--;
				i = canditer_next(&ci) - b->hseqbase;
				if (gids[i] >= min && gids[i] <= max)
					exists[gids[i] - min] = FALSE;
			}
		} else {
			while (ncand > 0) {
				ncand--;
				i = canditer_next(&ci) - b->hseqbase;
				exists[i] = FALSE;
			}
		}
		BATsetcount(res, ngrp);
		res->tkey = BATcount(res) <= 1;
		res->tsorted = BATcount(res) <= 1;
		res->trevsorted = BATcount(res) <= 1;
		res->tnil = false;
		res->tnonil = true;
	}

bailout:
	if (res && !msg)
		BBPkeepref(*ret = res->batCacheid);
	else if (res)
		BBPreclaim(res);
	if (b)
		BBPunfix(b->batCacheid);
	if (g)
		BBPunfix(g->batCacheid);
	if (e)
		BBPunfix(e->batCacheid);
	if (s)
		BBPunfix(s->batCacheid);
	return msg;
}
