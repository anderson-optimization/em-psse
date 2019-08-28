
# PSSE RAW

This packages parses PSSE RAW files in pandas dataframes.

## Alternative Packages

- [lanl-ansi/grg-pssedata](https://github.com/lanl-ansi/grg-pssedata)


## Overview

The program is composed of 

- `psse.py` 
	- Reads through the file and changes it's mode based on signals received.  
	- Stores the data based on the current mode
- `psse-modes.yaml` 
	- Describes the structure of the RAW format.  
	- Can create different mode files to describe different RAW versions (not currently implemented)
- `format_components.py`
	- An opinonated way to format the RAW data, based on [pypsa](https://pypsa.org/)

The current `psse-modes` file is for a specific RAW format.  There are no gaurentees that it parses the given format or any format correctly.  

If you are planning on using, __validate the output__.  

## Errors/Updates/Corrections

Submit any corrections or new modes and pull requests.

## Sample scripts

The following are examples of ways to use the module

- `parse.py` parses and prints data
- `network.py` performs simple network analysis
- `scripts/process.sh` processes folder of raw files

## Example Usage

```
python3 parse.py --input data/ERCOT_SS-18SSWG_2021_SUM1_Final_06252018.RAW  --debug

### Output
...
...
...
DEBUG:em.parse_raw:switchedshunt
DEBUG:em.parse_raw:
     I  MODSW  UK1  UK2  VSWHI  VSWLO  SWREM ...  B5  N6  B6  N7  B7  N8  B8
0    1      1    0    1   1.03   0.95      0 ... NaN NaN NaN NaN NaN NaN NaN
1   99      1    0    1   1.03   0.95      0 ... NaN NaN NaN NaN NaN NaN NaN
2  107      1    0    1   1.03   0.95      0 ... NaN NaN NaN NaN NaN NaN NaN
3  126      1    0    1   1.03   0.95      0 ... NaN NaN NaN NaN NaN NaN NaN
4  149      1    0    1   1.03   0.95      0 ... NaN NaN NaN NaN NaN NaN NaN

[5 rows x 26 columns]

DEBUG:em.parse_raw:zone
DEBUG:em.parse_raw:
   I      ZONAME
0  1  'TEMPORAR'
1  2  'BRYAN   '
2  3  'DENTON  '
3  4  'GARLAND '
4  5  'KOPPERL '

DEBUG:em.parse_raw:gen
DEBUG:em.parse_raw:
       I    ID     PG   QG     QT     QB ...   O3   F3  O4   F4  O5   F5
0    967  'V1'    0.0  0.0    1.0 -100.0 ...    0  1.0   0  1.0   0  1.0
1    967  'V2'    0.0  0.0    1.0 -100.0 ...    0  1.0   0  1.0   0  1.0
2   5920  'EQ'  599.4  0.0  360.0 -360.0 ...    0  1.0   0  1.0   0  1.0
3   6103  'EQ'  219.0  0.0  132.0 -132.0 ...    0  1.0   0  1.0   0  1.0
4  40426  'B1'    0.0  0.0   20.0  -20.0 ...    0  1.0   0  1.0   0  1.0

[5 rows x 28 columns]

DEBUG:em.parse_raw:multiline
DEBUG:em.parse_raw:
       I      J    ID  DUM1   DUM2  ...   DUM5  DUM6  DUM7  DUM8  DUM9
0   5568  42540  '&1'     1  43221  ...    NaN   NaN   NaN   NaN   NaN
1   5915  42530  '&1'     2  47531  ...    NaN   NaN   NaN   NaN   NaN
2  40010  40430  '&1'     1  40439  ...    NaN   NaN   NaN   NaN   NaN
3  40010  41330  '&1'     1  41440  ...    NaN   NaN   NaN   NaN   NaN
4  40015  40170  '&1'     1  40171  ...    NaN   NaN   NaN   NaN   NaN

[5 rows x 12 columns]

DEBUG:em.parse_raw:owner
DEBUG:em.parse_raw:
    I          OWNAME
0   1             '1'
1   9  'TAEPTC      '
2  11            '11'
3  12  'TAEPTN      '
4  18  'RAIRLG      '

DEBUG:em.parse_raw:facts
DEBUG:em.parse_raw:
   N      I  J  MODE  PDES  QDES  ...    LINX  RMPCT  OWNER  SET1  SET2  VSREF
0  1   9025  0     0   0.0   0.0  ...    0.05  100.0    190   0.0   0.0      0
1  2  11172  0     1   0.0   0.0  ...    0.05  100.0    794   0.0   0.0      0
2  3  11173  0     1   0.0   0.0  ...    0.05  100.0    794   0.0   0.0      0
3  4  80319  0     1   0.0   0.0  ...    0.05  100.0      9   0.0   0.0      0
4  5  80320  0     1   0.0   0.0  ...    0.05  100.0      9   0.0   0.0      0

[5 rows x 19 columns]

DEBUG:em.parse_raw:fixedshunt
DEBUG:em.parse_raw:
       I    ID  STATUS  UK1      B
0   5915  'R1'       0  0.0 -150.0
1   5915  'R2'       0  0.0 -150.0
2  38046  'C1'       1  0.0   20.0
3  38046  'C2'       1  0.0   20.0
4  38046  'C3'       1  0.0   20.0

DEBUG:em.parse_raw:twodc
DEBUG:em.parse_raw:
                I  MDC    RDC  SETVL  VSCHD  ...    ICI  IFI  ITI IDI  UK3-A
0  '1           '    1  0.000 -219.0   82.0  ...      0    0    0   1    0.0
1  '2           '    1  0.050  599.4  164.0  ...      0    0    0   1    0.0
2  '3           '    1  0.036 -149.0   42.2  ...      0    0    0   1    0.0
3  '4           '    1  0.036 -149.0   42.2  ...      0    0    0   1    0.0

[4 rows x 46 columns]

DEBUG:em.parse_raw:transformer
DEBUG:em.parse_raw:
     I    J      K   CKT  CW  CZ  ...    VMI3  NTP3  TAB3  CR3  CX3  UK5-A
0  240  241  36996  '2 '   1   1  ...     0.9  33.0   0.0  0.0  0.0    0.0
1  240  241  36997  '1 '   1   1  ...     0.9  33.0   0.0  0.0  0.0    0.0
2  973  834    974  '1 '   1   1  ...     0.9  33.0   0.0  0.0  0.0    0.0
3  977  979    957  '2 '   1   1  ...     0.9  33.0   0.0  0.0  0.0    0.0
4  977  976    958  '1 '   1   1  ...     0.9  33.0   0.0  0.0  0.0    0.0

[5 rows x 83 columns]

DEBUG:em.parse_raw:area
DEBUG:em.parse_raw:
   I  ISW  PDES  PTOL          ARNAME
0  1    0   0.0  10.0  'ONCOR_ED    '
1  2    0   0.0  10.0  'RYBRNTSP    '
2  3    0   0.0  10.0  'TEXLATSP    '
3  4    0   0.0  10.0  'CNP_TSP     '
4  5    0   0.0  10.0  'CPS_TSP     '

DEBUG:em.parse_raw:branch
DEBUG:em.parse_raw:
   I    J   CKT         R         X        B ...   O2   F2  O3   F3  O4   F4
0  1    5  '1 '  0.002788  0.014900  0.00415 ...    0  1.0   0  1.0   0  1.0
1  1   11  '1 '  0.005850  0.030030  0.00832 ...    0  1.0   0  1.0   0  1.0
2  2    4  '1 '  0.004453  0.023790  0.00665 ...    0  1.0   0  1.0   0  1.0
3  2   13  '1 '  0.000332  0.003062  0.00091 ...    0  1.0   0  1.0   0  1.0
4  2  964  '1 '  0.000660  0.005760  0.00536 ...    0  1.0   0  1.0   0  1.0

[5 rows x 24 columns]

DEBUG:em.parse_raw:bus
DEBUG:em.parse_raw:
   I            NAME  BASKV  IDE  AREA  ...          VA  AMAX  AMIN  BMAX  BMIN
0  1  'ROANSPRARE  '  138.0    1    11  ...   69.709279  1.05  0.95  1.05  0.95
1  2  'KEITHSW     '  138.0    1    11  ...   69.756469  1.05  0.95  1.05  0.95
2  4  'IOLA        '  138.0    1    11  ...   69.975923  1.05  0.95  1.05  0.95
3  5  'SANDYSW     '  138.0    1    11  ...   69.697614  1.05  0.95  1.05  0.95
4  6  'HWY6        '  138.0    1    11  ...   67.540633  1.05  0.95  1.05  0.95

[5 rows x 13 columns]

DEBUG:em.parse_raw:load
DEBUG:em.parse_raw:
   I    ID  STATUS  AREA  ZONE     PL     QL   IP   IQ   YP   YQ  OWNER  A  B
0  1  '1 '       1    11    11  7.626  2.961  0.0  0.0  0.0  0.0    115  1  0
1  4  '1 '       1    11    11  7.807  0.835  0.0  0.0  0.0  0.0    115  1  0
2  6  '1 '       1    11    11  5.095  1.523  0.0  0.0  0.0  0.0    115  1  0
3  7  '1 '       1    11    11  8.897  1.020  0.0  0.0  0.0  0.0    115  1  0
4  8  '1 '       1    11    11  3.709  0.831  0.0  0.0  0.0  0.0    115  1  0
```


### Example jq join

```
jq -s '.[0] * .[1]' bus-ercot_ss-18sswg_2021_sum1.json line-ercot_ss-18sswg_2021_sum1.json > ercot_ss-18sswg_2021_sum1.json
```