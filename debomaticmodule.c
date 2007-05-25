/* Deb-o-Matic
 *
 * Copyright (C) 2007 Luca Falavigna
 *
 * Author: Luca Falavigna <dktrkranz@ubuntu.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; only version 2 of the License
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

#include <Python.h>

static PyObject *debomatic_daemon(PyObject *self, PyObject *args)
{
	daemon(1, 0);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef DebomaticMethods[] = {
	{"daemon",  debomatic_daemon, METH_VARARGS, "Daemonize debomatic."},
	{NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initdebomatic(void)
{
    (void)Py_InitModule("debomatic", DebomaticMethods);
}

int main(int argc, char *argv[])
{
	Py_SetProgramName(argv[0]);
	Py_Initialize();
	initdebomatic();
	return 0;
}
