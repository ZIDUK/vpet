#pragma once
#include_next <sys/time.h>
int coordinatorSetTime(const timeval*,const void*);
#define settimeofday coordinatorSetTime
