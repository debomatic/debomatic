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
