cimport cnoisepy
from libc.stdint cimport int16_t, int32_t
from cpython.bytes cimport PyBytes_FromStringAndSize
from libcpp cimport bool

cdef class noisepy:
    cdef cnoisepy.AcousticIndicatorsData* _c_noisepy
    cdef bool a_filter
    cdef float ref_pressure
    def __cinit__(self):
        self._c_noisepy = cnoisepy.ai_NewAcousticIndicatorsData()
        if self._c_noisepy is NULL:
            raise MemoryError()
        cnoisepy.ai_InitAcousticIndicatorsData(self._c_noisepy)

    def __dealloc__(self):
        if self._c_noisepy is not NULL:
            cnoisepy.ai_FreeAcousticIndicatorsData(self._c_noisepy)

    def __init__(self, a_filter, ref_pressure):
        self.a_filter = a_filter
        self.ref_pressure = ref_pressure

    def push(self, unsigned char* python_samples, int length):
      cdef float laeq = 0.0
      if cnoisepy.ai_AddSample(self._c_noisepy, length, <int16_t*>python_samples , &laeq, self.ref_pressure, self.a_filter):
        return laeq
