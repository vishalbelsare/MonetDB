/* -*- c-basic-offset:4; c-indentation-style:"k&r"; indent-tabs-mode:nil -*- */

/**
 * @file
 *
 * Declarations for semantics/functions.c; Data structures and access
 * functions for XQuery function calls and definitions.
 *
 *
 * Copyright Notice:
 * -----------------
 *
 * The contents of this file are subject to the Pathfinder Public License
 * Version 1.1 (the "License"); you may not use this file except in
 * compliance with the License.  You may obtain a copy of the License at
 * http://monetdb.cwi.nl/Legal/PathfinderLicense-1.1.html
 *
 * Software distributed under the License is distributed on an "AS IS"
 * basis, WITHOUT WARRANTY OF ANY KIND, either express or implied.  See
 * the License for the specific language governing rights and limitations
 * under the License.
 *
 * The Original Code is the Pathfinder system.
 *
 * The Initial Developer of the Original Code is the Database &
 * Information Systems Group at the University of Konstanz, Germany.
 * Portions created by the University of Konstanz are Copyright (C)
 * 2000-2005 University of Konstanz.  All Rights Reserved.
 *
 * $Id$
 */

#ifndef FUNCTIONS_H

typedef struct PFfun_t PFfun_t;

#define FUNCTIONS_H

#include "pathfinder.h"
/* PFty_t */
#include "types.h"
/* PFenv_t */
#include "env.h"

/* PFvar_t */
#include "variable.h"

/* PFcnode_t */
#include "core.h"

#include "core2alg.h"

/** Data structure to hold information about XQuery functions.  */
/* typedef struct PFfun_t PFfun_t; */

/**
 * Data structure to hold information about XQuery functions.
 * Functions can be either predefined (builtin, XQuery F&O) functions or
 * user-defined.
 *
 * @note
 * As of the <a href="http://www.w3.org/TR/2002/WD-xquery-20020816/">Aug
 * 2002 W3C draft</a> (sec. 4.5), XML Query does not allow function
 * overloading for user-defined functions. Recursion, however, is
 * allowed.
 */
struct PFfun_t {
    PFqname_t      qname;      /**< function name */
    unsigned int   arity;      /**< number of arguments */
    bool           builtin;    /**< is this a builtin (XQuery F&O) function? */
    PFty_t        *par_ty;     /**< builtin: array of formal parameter types */
    PFty_t         ret_ty;     /**< builtin: return type */
    struct PFla_pair_t (*alg) (const struct PFla_op_t *, struct PFla_pair_t *);
    PFvar_t      **params;     /**< list of parameter variables */
    PFcnode_t     *core;
    int            fid;        /**< id for variable environment mapping (summer_branch) */
    char          *sig;        /**< milprint_summer: full signature converted to single identifier */	
};

/**
 * Environment of functions known to Pathfinder.
 */
extern PFenv_t *PFfun_env;

/** allocate a new struct to describe a (built-in or user) function */
PFfun_t *PFfun_new (PFqname_t, unsigned int, bool, PFty_t *, PFty_t *,
                    struct PFla_pair_t (*alg) (const struct PFla_op_t *,
                                               struct PFla_pair_t *),
                    PFvar_t **params);

#endif   /* FUNCTIONS_H */

/* vim:set shiftwidth=4 expandtab: */
