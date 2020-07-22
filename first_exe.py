from glob import glob
import pandas as pd
import numpy as np

def read_data(path):
  global col_names

  day_col = col_names[0]
  hh = col_names[1]
  mm = col_names[2]
  ss = col_names[3]

  helios = int(path[-14])
  decade = path[-13:-11]
  day = path[-10:-7]

  data = pd.read_csv(path, names=col_names, delim_whitespace=True,
                     na_values=-1, converters={hh: str, mm: str, ss: str})

  date = decade + ' ' + day + ' ' + data[hh] + ':' + data[mm] + ':' + data[ss]

  data.insert(0, 'Datetime', date)
  data.insert(1, 'Helios', helios)
  data.drop([day_col, hh, mm, ss], axis='columns', inplace=True)

  return data

col_names = ['day', 'hh', 'mm', 'ss', 'rh', 'esh', 'clong', 'clat',
             'crot', 'np1', 'vp1', 'Tp1', 'vaz', 'vel', 'Bx', 'By', 'Bz',
             'sBx', 'sBy', 'sBz', 'nal', 'val', 'Tal', 'np2', 'vp2', 'Tp2']

helios_paths = glob('Helios/*ord.txt')
shock_path = 'Shock_list_CMEs.xls'

data = pd.concat([read_data(path) for path in helios_paths],
                 ignore_index=True, verify_integrity=True)

data['np2'].replace('******', float('nan'), inplace=True)
data['np2'] = data['np2'].astype(float)

data['Datetime'] = pd.to_datetime(data['Datetime'], format='%y %j %H:%M:%S')
data.sort_values('Datetime', inplace=True)
data.set_index('Datetime', inplace=True)

bx = data['Bx']
by = data['By']
bz = data['Bz']
btotal = np.sqrt(bx ** 2 + by ** 2 +  bz ** 2)
btotal_pos = data.columns.get_loc('Bz') + 1

data.insert(btotal_pos, 'Btotal', btotal)

data.to_csv('helios_data.csv', na_rep='NaN')

date_parser = lambda date: pd.to_datetime(date, format='%d.%m.%y %H:%M')
shock_list = pd.read_excel(shock_path, parse_dates=['Date/time'], date_parser=date_parser)

shock_list.rename({col: col.strip() for col in shock_list.columns}, axis='columns', inplace=True)
shock_list.rename({'SC': 'Helios', 'Date/time': 'Datetime'}, axis='columns', inplace=True)
shock_list.drop(['JJ', 'TT', 'SS', 'MM'], axis='columns', inplace=True)

shock_list.sort_values('Datetime', inplace=True)
shock_list.set_index('Datetime', inplace=True)

shock_list['Helios'] = shock_list['Helios'].apply(lambda helios: int(helios[1]))

shock_list.to_csv('shock_list.csv', na_rep='NaN')
