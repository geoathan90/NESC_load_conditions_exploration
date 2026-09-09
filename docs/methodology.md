# ERA5 winter numerical-analysis methodology

## Observation population

The pipeline concatenates observations by their decoded timestamps. It does not
relabel or aggregate them into named meteorological winters. A timestamp is unique
at the domain level; each timestamp–latitude–longitude combination is one
grid-cell-hour.

Validation constructs every expected hourly timestamp within each configured
calendar month. The intentionally absent months are not errors. Event detection
requires adjacent samples to differ by exactly one hour, which prevents the
March–November gap from connecting otherwise adjacent array positions. True
December-to-January continuity across annual files is retained.

## Variables and conversions

Raw ERA5 fields are retained in the derived NetCDF. Additional fields are:

| Derived variable | Definition |
| --- | --- |
| `t2m_c` | `t2m - 273.15` |
| `d2m_c` | `d2m - 273.15` |
| `dewpoint_depression_c` | `t2m_c - d2m_c` |
| `precip_rate_mmh` | `avg_tprate × 3600` |
| `snowfall_rate_mmh` | `avg_tsrwe × 3600` |
| `low_cloud_cover_pct` | `lcc × 100` |

The water-equivalent flux conversion uses `1 kg m-2 = 1 mm` water depth. `tcslw`,
`cbh` and `fg10` retain kg/m², m and m/s respectively.

## Precipitation categories

Categories follow [ECMWF/WMO GRIB2 Code Table 4.201](https://codes.ecmwf.int/grib/format/grib2/ctables/4/201/)
and the [ECMWF ptype parameter description](https://codes.ecmwf.int/grib/param-db/260015).

- `freezing_liquid`: freezing rain (3) or freezing drizzle (12)
- `wet_snow`: wet snow (6)
- `accretion_relevant`: freezing rain (3), wet snow (6), or freezing drizzle (12)

Ice pellets (8) and ordinary snow (5) are reported as background categories but
are not included in `accretion_relevant`. `ptype` remains categorical and is never
interpolated.

Occurrence percentages use two explicit denominators: all valid grid-cell-hours,
and `ptype != 0` grid-cell-hours. ECMWF advises using instantaneous `ptype` with
precipitation rate. Because timing/packing and trace precipitation can yield a type
flag with a very low interval-mean rate, the pipeline reports illustrative 0, 0.01
and 0.1 mm/h sensitivity cases without adopting either positive cutoff as a final
scientific definition.

## Events

An event is a consecutive run of unfiltered `accretion_relevant` samples at one
grid cell. Events are deliberately cell-specific; a single synoptic episode may
therefore appear in multiple rows. For each event the table preserves times,
ptype composition, temperatures, gusts, rates, one-hour water-equivalent sums and
TCSLW. These are candidate meteorological episodes, not verified conductor icing.

## Validation contract

The run fails on a missing file/variable, unrecognized ptype value, invalid or
duplicate timestamp, missing expected hour, unexpected hour, wrong spatial bound
or 0.25° spacing, wrong variable dimensions/units/GRIB step type, auxiliary-coordinate
disagreement, instant/avg/max misalignment, or cross-year grid inconsistency.

No exception is swallowed. `expver` and scalar `number` coordinates are compared
before merging and retained only when consistent.

NetCDF input/output uses the `h5netcdf`/`h5py` backend pinned in
`requirements.txt`, avoiding dependence on system NetCDF libraries.
