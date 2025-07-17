#ifndef LIDAR_H
#define LIDAR_H

/* Distance in cm of the nearest obstacle in the scan, or -1 when the scan is empty. */
int lidar_nearest_cm(const int *scan, int count);

#endif
