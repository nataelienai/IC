from matplotlib import pyplot as plt
from matplotlib import dates
from matplotlib import units
import pandas as pd
import numpy as np
import datetime
import os

FORMATS = ['%Y', '%b', '%d', '%H:%M', '%H:%M', '%S.%f']
ZERO_FORMATS = ['', '%b\n%Y', '%d %b', '%d %b', '%H:%M', '%H:%M']
OFFSET_FORMATS = ['', '%Y', '%b %Y', '%d %b %Y', '%d %b %Y', '%d %b %Y %H:%M']

converter = dates.ConciseDateConverter(formats=FORMATS,
                                       zero_formats=ZERO_FORMATS,
                                       offset_formats=OFFSET_FORMATS)

units.registry[np.datetime64] = converter
units.registry[datetime.date] = converter
units.registry[datetime.datetime] = converter

SMALL_SIZE = 12
MEDIUM_SIZE = 14

plt.rc('font', size=SMALL_SIZE)
plt.rc('axes', labelsize=MEDIUM_SIZE)
plt.rc('xtick', labelsize=SMALL_SIZE)
plt.rc('ytick', labelsize=SMALL_SIZE)
plt.rc('legend', fontsize=MEDIUM_SIZE)
plt.rc('figure', autolayout=True)
plt.rc('axes', grid=True)
plt.rc('legend', loc='upper left', borderaxespad=0)

BASE_UNITS = {'rh':'AU', 'esh':'deg', 'clong':'deg', 'clat':'deg', 
              'crot':'#', 'np1':'cm-3', 'vp1':'km/s', 'Tp1':'K', 
              'vaz':'deg', 'vel':'deg', 'Bx':'nT', 'By':'nT',
              'Bz':'nT', 'Btotal':'nT', 'sBx':'nT', 'sBy':'nT',
              'sBz':'nT', 'nal':'cm-3', 'val':'km/s', 'Tal':'K',
              ' np2':'cm-3', 'vp2':'km/s', 'Tp2':'K'}

DESIRED_GRAPHS = ['np1', 'vp1', 'Tp1', 'Bx', 'By', 'Bz', 'Btotal']
HELIOS_COLS = ['Datetime', 'Helios'] + DESIRED_GRAPHS
SHOCK_COLS = ['Datetime', 'Helios']
COLORS = ['#0080ff', '#ff6f00', '#000000']

WIDTH_PER_SUBPLOT = 1.85
HEIGHT_PER_SUBPLOT = 2.1

HELIOS_FILEPATH = 'helios_data.csv'
SHOCK_FILEPATH = 'shock_list.csv'

def reconstruct_gap(series):
  data = pd.Series(dtype='float64', name=series.name)
  indexes = series.index
  in_nan_sequence = False
  for index, next_index in zip(indexes[:-1], indexes[1:]):
    if isinstance(series[next_index], pd.Series):
      is_nan = series[next_index].isnull().any()
    else:
      is_nan = np.isnan(series[next_index])
    if is_nan:
      if not in_nan_sequence:
        start = index
        in_nan_sequence = True
    else:
      if in_nan_sequence:
        end = next_index
        in_nan_sequence = False
        nan_seq = series[start:end]
        if pd.isna(nan_seq[0]):
          continue
        nan_seq = nan_seq.interpolate(method='time', limit_direction='both')
        data = data.append(nan_seq)
        last_datetime = nan_seq.index[-1] + pd.Timedelta(1, 'sec')
        last_value = np.nan
        data = data.append(pd.Series(last_value, [last_datetime], name=data.name))
  return data

# Programa Principal

try:
  os.mkdir("Graphs")
except FileExistsError:
  print("Diretório 'Graphs' já existe!")
else:
  print("Diretório 'Graphs' criado com sucesso!")

helios_data = pd.read_csv(HELIOS_FILEPATH, usecols=HELIOS_COLS,
                          index_col='Datetime', parse_dates=['Datetime'])
shock_list = pd.read_csv(SHOCK_FILEPATH, usecols=SHOCK_COLS,
                         parse_dates=['Datetime'])

nsubplots = len(DESIRED_GRAPHS)
fig_width = nsubplots * WIDTH_PER_SUBPLOT
fig_height = nsubplots * HEIGHT_PER_SUBPLOT
fig = plt.figure(figsize=(fig_width, fig_height))
axes = fig.subplots(nrows=nsubplots, ncols=1, sharex=True)

shock_timedelta = pd.to_timedelta(3, 'days')

for shock_index in range(len(shock_list)):
  shock_time = shock_list['Datetime'][shock_index]
  helios = shock_list['Helios'][shock_index]
  period_start = (shock_time - shock_timedelta)
  period_end = (shock_time + shock_timedelta)

  interval = helios_data[period_start:period_end]
  filter_by = (interval['Helios'] == helios)
  filtered_data = interval[filter_by]

  for ax_index, variable in enumerate(DESIRED_GRAPHS):
    specific_data = filtered_data[variable]
    x = specific_data.index
    y = specific_data.values
    axes[ax_index].plot_date(x, y, label=f"Hélios {helios}",
                             linestyle='-', marker=None,
                             color=COLORS[0])
    
    gap = reconstruct_gap(specific_data)
    axes[ax_index].plot_date(gap.index, gap.values, label='Reconstrução',
                             color=COLORS[1], linestyle='-', marker=None)
    
    axes[ax_index].axvline(shock_time, label='Choque', color=COLORS[2],
                           linewidth=2.2, linestyle='--')
    axes[ax_index].set_ylabel(f'{variable} ({BASE_UNITS[variable]})')
  
  left_xlim = period_start
  right_xlim = period_end
  axes[-1].set_xlim(left_xlim, right_xlim)

  axes[0].legend(bbox_to_anchor=(1.01, 1), shadow=True)
  
  fig.align_ylabels()
  fig.savefig(f'Graphs/{shock_index}')
  for ax in axes:
    ax.clear()
plt.close(fig)
