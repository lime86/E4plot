import matplotlib.pyplot as plt
import numpy as np
from scipy import stats, constants
import os
import math


class Data:

    # create a data object with empty values
    def __init__(self):
        self.filled = False
        self.repeats = None
        self.n = []
        self.type = ''
        self.name = ''
        self.time = []
        self.v_mean = []
        self.i_mean = []
        self.i_error = []
        self.c_mean = []
        self.c_error = []
        self.inverse_c_squared = []
        self.inverse_c_squared_error = []
        self.temperature = []
        self.humidity = []

    # read a file and fill data
    def extract_data(self, filename, average):
        self.filled = True

        # If a name has not been specified, find the name
        if self.name == '':
            path, file = os.path.split(filename)
            self.name, ext = os.path.splitext(file)

        # If the data type has not been specified, find the type
        if self.type == '':
            self.find_type()

        # Extract data from a IV data file
        if self.type == 'iv':

            self.n = np.genfromtxt(fname=filename, dtype=float, usecols=1, skip_header=1).tolist()
            T = np.genfromtxt(fname=filename, dtype=float, usecols=0, skip_header=1).tolist() # time
            v = np.genfromtxt(fname=filename, dtype=float, usecols=2, skip_header=1).tolist() # voltage
            i = np.genfromtxt(fname=filename, dtype=float, usecols=3, skip_header=1).tolist() # current
            t = np.genfromtxt(fname=filename, dtype=float, usecols=4, skip_header=1).tolist() # temperature
            h = np.genfromtxt(fname=filename, dtype=float, usecols=5, skip_header=1).tolist() # humidity

            # Find how many measurements were taken at each voltage
            self.find_repeats()

            # Find time at each set of measurements
            time_convert = []
            for x in range(0, len(T)):
                time_convert.append(T[x]-T[0])
            for x in range(0, len(time_convert), self.repeats):
                self.time.append((sum(time_convert[x:x + self.repeats]) / self.repeats))
            # Average voltage for each measurement
            for x in range(0, len(v), self.repeats):
                self.v_mean.append((sum(v[x:x + self.repeats]) / self.repeats))
            # Average current at each measurement
            if average == 'mean':
                for x in range(0, len(i), self.repeats):
                    self.i_mean.append((sum(i[x:x + self.repeats]) / self.repeats))
            elif average == 'median':
                for x in range(0, len(i), self.repeats):
                    i_section = i[x:x + self.repeats]
                    i_section.sort()
                    if self.repeats % 2 == 0.5:
                        p = int((self.repeats / 2) - 0.5)
                        self.i_mean.append(i_section[p])
                    elif self.repeats % 2 == 0:
                        p = int((self.repeats / 2) - 1)
                        self.i_mean.append(((i_section[p] + i_section[p + 1]) / 2))
            # Standard error at each measurement
            for x in range(0, len(i), self.repeats):
                self.i_error.append(stats.sem(i[x:x + self.repeats]))
            # Average temperature at each measurement
            for x in range(0, len(t), self.repeats):
                self.temperature.append((sum(t[x:x + self.repeats]) / self.repeats))
            # Average humidity at each measurement
            for x in range(0, len(h), self.repeats):
                self.humidity.append((sum(h[x:x + self.repeats]) / self.repeats))

        # Extract data from CV file
        elif self.type == 'cv':

            self.n = np.genfromtxt(fname=filename, dtype=float, usecols=1, skip_header=2).tolist()
            T = np.genfromtxt(fname=filename, dtype=float, usecols=0, skip_header=2).tolist()
            v = np.genfromtxt(fname=filename, dtype=float, usecols=2, skip_header=2).tolist()
            c = np.genfromtxt(fname=filename, dtype=float, usecols=4, skip_header=2).tolist()
            t = np.genfromtxt(fname=filename, dtype=float, usecols=6, skip_header=2).tolist()
            h = np.genfromtxt(fname=filename, dtype=float, usecols=7, skip_header=2).tolist()

            # Find how many measurements were taken at each voltage
            self.find_repeats()

            # Find time at each set of measurements
            time_convert = []
            for x in range(0, len(T)):
                time_convert.append(T[x] - T[0])
            for x in range(0, len(time_convert), self.repeats):
                self.time.append((sum(time_convert[x:x + self.repeats]) / self.repeats))
            # Average voltage for each measurement
            for x in range(0, len(v), self.repeats):
                self.v_mean.append((sum(v[x:x + self.repeats]) / self.repeats))
            # Remove any capacitance values that are mistakes i.e. when the machine records ~9e49
            for x in range(0, len(c), self.repeats):
                c_repeats = c[x:x + self.repeats]
                c_final = []
                for y in range(0, len(c_repeats)):
                    if c_repeats[y] < 1e50:
                        c_final.append(c_repeats[y])
                self.c_error.append(stats.sem(c_final))
                # Find the average capacitance values
                if average == 'mean':
                    self.c_mean.append((sum(c_final) / len(c_final)))
                elif average == 'median':
                    c_final.sort()
                    if len(c_final) % 2 == 0.5:
                        p = int((len(c_final) / 2) - 0.5)
                        self.c_mean.append(c_final[p])
                    elif len(c_final) % 2 == 0:
                        p = int((len(c_final) / 2) - 1)
                        # print(p)
                        self.c_mean.append(((c_final[p] + c_final[p + 1]) / 2))
            # Find  average 1/C squared
            for x in range(0, len(self.c_mean)):
                self.inverse_c_squared.append(1 / self.c_mean[x] ** 2)
            # Propagate the errors
            for x in range(0, len(self.inverse_c_squared)):
                self.inverse_c_squared_error.append(abs((self.inverse_c_squared[x] * 2 * (self.c_error[x] / self.c_mean[x]))))
            # Average temperature at each measurement
            for x in range(0, len(t), self.repeats):
                self.temperature.append((sum(t[x:x + self.repeats]) / self.repeats))
            # Average humidity at each measurement
            for x in range(0, len(h), self.repeats):
                self.humidity.append((sum(h[x:x + self.repeats]) / self.repeats))

        # Extract Data from It file
        elif self.type == 'it':

            self.n = np.genfromtxt(fname=filename, dtype=float, usecols=1, skip_header=1).tolist()
            T = np.genfromtxt(fname=filename, dtype=float, usecols=0, skip_header=1).tolist()
            v = np.genfromtxt(fname=filename, dtype=float, usecols=2, skip_header=1).tolist()
            i = np.genfromtxt(fname=filename, dtype=float, usecols=3, skip_header=1).tolist()
            t = np.genfromtxt(fname=filename, dtype=float, usecols=4, skip_header=1).tolist()
            h = np.genfromtxt(fname=filename, dtype=float, usecols=5, skip_header=1).tolist()

            # Find how many measurements were taken at each voltage
            self.find_repeats()

            # Find time at each set of measurements
            time_convert = []
            for x in range(0, len(T)):
                time_convert.append(T[x] - T[0])
            for x in range(0, len(time_convert), self.repeats):
                self.time.append((sum(time_convert[x:x + self.repeats]) / self.repeats))
            # Average voltage for each measurement
            for x in range(0, len(v), self.repeats):
                self.v_mean.append((sum(v[x:x + self.repeats]) / self.repeats))
            # Average current at each measurement - for It the machine records in amps, hence *1000000
            if average == 'mean':
                for x in range(0, len(i), self.repeats):
                    self.i_mean.append((sum(i[x:x + self.repeats]) / self.repeats))
            elif average == 'median':
                for x in range(0, len(i), self.repeats):
                    i_section = i[x:x + self.repeats]
                    i_section.sort()
                    if self.repeats % 2 == 0.5:
                        p = int((self.repeats / 2) - 0.5)
                        self.i_mean.append(i_section[p])
                    elif self.repeats % 2 == 0:
                        p = int((self.repeats / 2) - 1)
                        #print(p)
                        self.i_mean.append(((i_section[p] + i_section[p + 1]) / 2))
            # Standard error at each measurement
            for x in range(0, len(i), self.repeats):
                ### check why ddof=0: std calculated by dividing (samplesize - ddof).
                ### ddof = 0: for biased estimator (population), ddof = 1: for unbiased estimator.
                ### unbiased estimator overestimates error
                ### sample is a subset of population
                ### A biased estimator is one that deviates from the true population value. An unbiased estimator is one that does not deviate from the true population parameter.
                self.i_error.append(stats.sem(i[x:x + self.repeats], ddof=0, nan_policy='omit'))
            # Average temperature at each measurement
            for x in range(0, len(t), self.repeats):
                self.temperature.append((sum(t[x:x + self.repeats]) / self.repeats))
            # Average humidity at each measurement
            for x in range(0, len(h), self.repeats):
                self.humidity.append((sum(h[x:x + self.repeats]) / self.repeats))

        else:
            print('Error: Unsure of the data type')

    # Decide if file is cv, iv or it
    def find_type(self):
        if 'iv' in self.name.lower():
            self.type = 'iv'
        elif 'cv' in self.name.lower():
            self.type = 'cv'
        elif 'it' in self.name.lower():
            self.type = 'it'
            #and not ('cv' or 'iv' or 'vi' or 'vc')

    # find how many repeat measurements were done
    def find_repeats(self):
        x = 0
        measurements = 0
        for i in range(len(self.n)):
            if x == self.n[i]:
                measurements += 1
            else:
                break
        self.repeats = measurements

    # find average temperature
    def average_temp(self):
        average_temperature = Data.round_sig(sum(self.temperature) / len(self.temperature), 3)
        temperature_error = Data.round_sig(stats.sem(self.temperature), 1)
        return average_temperature, temperature_error

    # find average humidity
    def average_hum(self):
        average_humidity = Data.round_sig(sum(self.humidity) / len(self.humidity), 3)
        humidity_error = Data.round_sig(stats.sem(self.humidity), 1)
        return average_humidity, humidity_error

    # Remove a specific point from the data - not currently usable in the Plot_Multiple/Single
    def remove_anomalies(self, index):
        if self.type == 'iv':
            del self.v_mean[index]
            del self.i_mean[index]
            del self.i_error[index]
            del self.time[index]
            del self.temperature[index]
            del self.humidity[index]

        elif self.type == 'cv':
            del self.v_mean[index]
            del self.c_mean[index]
            del self.c_error[index]
            del self.inverse_c_squared[index]
            del self.inverse_c_squared_error[index]

        if self.type == 'it':
            del self.v_mean[index]
            del self.i_mean[index]
            del self.i_error[index]
            del self.time[index]
            del self.temperature[index]
            del self.humidity[index]

    # convert time
    def time_to_minutes(self):
        for x in range(0, len(self.time)):
            self.time[x] = self.time[x]/60

    def time_to_hours(self):
        for x in range(0, len(self.time)):
            self.time[x] = self.time[x]/3600

    def time_to_days(self):
        for x in range(0, len(self.time)):
            self.time[x] = self.time[x]/(24*3600)

    # return properties
    def get_name(self):
        return self.name

    def get_time(self, type='hours'):
        if type == 'hours':
            self.time_to_hours()
            return self.time
        elif type == 'minutes':
            self.time_to_minutes()
            return self.time
        elif type == 'days':
            self.time_to_days()
            return self.time
        else:
            return self.time

    def get_voltage(self):
        return self.v_mean

    def get_current(self):
        return self.i_mean

    ## normalise leakage current to 20 degreeC
    def normalise(self):
        for index, value in enumerate(self.i_mean):
            self.i_mean[index] = self.normalise_current(value, self.temperature[index])

    def normalise_current(self, current, temp):
        Eg = 1.124 ##eV, PhD thesis
        T1 = temp+273.15 ## measurement temperature
        T2 = 293.15 ## temperature to be normalised to
        i_norm = current*((T1/T2)**2)*np.exp(-(Eg/(2*constants.physical_constants["Boltzmann constant in eV/K"][0]))*(1/T2-1/T1)) ## scipy.constants.physical_constants
        return i_norm

    def get_current_error(self):
        return self.i_error

    def get_inverse_capacitance(self):
        return self.inverse_c_squared

    def get_inverse_capacitance_error(self):
        return self.inverse_c_squared_error

    def get_temperature(self):
        return self.temperature

    def get_humidity(self):
        return self.humidity

    # print properties
    def print_voltage(self):
        print(self.v_mean)

    def print_current(self):
        print(self.i_mean)

    def print_current_error(self):
        print(self.i_error)

    def print_temperature(self):
        print(self.temperature)

    def print_humidity(self):
        print(self.humidity)

    def print_average_temperature(self):
        print(self.average_temp())

    def print_average_humidity(self):
        print(self.average_hum())

    def print_name(self):
        print(self.name)

    # Round numbers to specified significant figures
    def round_sig(x, sig=2):
        return round(x, sig - int(math.floor(math.log10(abs(x)))) - 1)
