from collections import deque
from math import sqrt

SWING_HIGH_W = 3  # threshold for angular acceleration for swing detect in rad/sec
SWING_LOW_W = 2  # threshols for angular acceleration for end of swing detect in rad/sec
SWING_PROCENT = 0.2  # percent to end swing
SWING_TIME = 5  # number of measurements to detect swing
SWING_TIME_END = 3  # number of measurements to leave swing
SWING_CIRCLE_TIME = 350  # time const for swing in circle
SWING_CIRCLE_W = 25  # angilar velocity treshold for swing in circles
# SWING_HIGH_A = 350  #threshold for accelerometer for swing detection in m/s
# SWING_LOW_A = 225 #threshold for accelerometer for end of swing detection in m/s
STAB_TIME = 5  # number of measurements to detect stab
STAB_LOW_W = 2  # low threshold for angular velocity for stab detect in рад2/c2
STAB_HIGH_A = 100  # threshold for acceleration for stab detect in m2/s4
STAB_PAUSE = 15
STAB_SCALAR_LEVEL = -200  # scalar product level

HIT_HIGH_A = 600  # threshols for acceleration for hit detect in CU
HIT_TIME = 5  # number of measurements to detect hit using acceleration
HIT_PAUSE = 15  # minimal time pause between different hits
HIT_SCALAR_LEVEL = -200  # scalar product level
HIT_LOW_W = 2

SPIN_TIME = 50  # time to start spin
SPIN_COUNTER = 4  # number of swings to start spin
SPIN_W = 50  # level of angular velocity to start spin
SPIN_CIRCLE_TIME = 200  # time const for spin
SPIN_LOW_W = 40  # threshold to leave spin


def update_acc_data(parameters: dict, actions: dict, a_curr: float, time: int):
    """
    Function updates acceleration parameters: start ans state of acceleration rising
    :param parameters: dict with parameters
    :param a_curr: current acceleration data
    :param actions: list of actions states
    :param time time count
    :return:
    """
    # print("a = %i, time = %i" % (a_curr, time))
    if a_curr >= HIT_HIGH_A:
        parameters['a_hit_start'] = time
    # param for starting swing with acc
    """if a_curr >= SWING_HIGH_A and parameters['a_swing'] == 0: 
        parameters['a_swing_start'] = time
        parameters['a_swing'] = 1
    #param to end swing with acc
    if a_curr < SWING_LOW_A:
        parameters['a_swing'] = 0
        parameters['a_swing_start'] = -1"""
    # params for stab
    if a_curr >= STAB_HIGH_A:
        parameters['a_stab_start'] = time
    """if a_curr < STAB_HIGH_A:
        parameters['a_stab'] = 0
        actions['stab'] = 0"""


def update_gyro_data(parameters: dict, actions: dict, w_curr: float, time: int):
    """
    this function updates parameters that depend of gyroscope
    :param parameters: dict with parameters
    :param actions: dict with states
    :param w_curr: current angular velocity
    :param time time counter
    :return:
    """
    if not actions['swing']:
        if parameters['w_prev'] < w_curr and parameters['w_rising'] == 0:
            parameters['w_rising'] = 1
            parameters['w_start'] = time
    if w_curr < SWING_LOW_W:
        parameters['w_swing'] = 0
    else:
        parameters['w_swing'] = 1
    if parameters['w_prev'] > w_curr:
        parameters['w_rising'] = 0
        parameters['w_start'] = -1
    if w_curr > HIT_LOW_W:
        parameters['w_hit'] = time
        """actions['swing'] = 0"""
    """if w_curr < STAB_LOW_W and parameters['w_low'] == 0:
        parameters['w_low_start'] = time
        parameters['w_low'] = 1"""
    if w_curr > STAB_LOW_W:
        parameters['w_high_stab'] = time
        actions['stab'] = 0
        # print("w = %f, started to rise = %i" % (w_curr, parameters['w_start']))


def check_hit_with_accelerometer_and_change(acc_data: deque, time: int, parameters: dict, hit: int) -> bool:
    """
    this function detects hits using high acceleration above HIT_HIGH_A
    :param acc_data: 10 last accelerometer measurements
    :param time: current time counter
    :param parameters:  parameters of system
    :param hit: state of hit action
    :return:
    """
    # print(parameters['a_hit_start'], time)
    if (time - parameters['a_hit_start']) < HIT_TIME and (time - parameters['w_hit'] < HIT_TIME):
        """if hit == 0 and (not parameters['hit_starts'] or time - parameters['hit_starts'][-1] > HIT_PAUSE):
            print('HIT! at %i' % time)
            if not time in parameters['hit_starts']:
                parameters['hit_starts'].append(time)
            return 1"""
        change = 0
        for i in range(min(HIT_TIME - 1, len(acc_data) - 1)):
            mul = sum([acc_data[9][j] * acc_data[9 - i][j] for j in range(3)])
            if mul < HIT_SCALAR_LEVEL:
                change += 1
            if change > 0 and hit == 0 and (
                        not parameters['hit_starts'] or time - parameters['hit_starts'][-1] > HIT_PAUSE):
                print('HIT! at %i' % time)
                if time not in parameters['hit_starts']:
                    parameters['hit_starts'].append(time)
                return True
        if change == 0:
            return False
    return False


def check_hit_with_change(acc_data: deque, time: int, parameters, hit) -> bool:
    """
    Function detects if accelerometer data in acc_data contains hit
    hit as detected as more than one change of acceleration orientation through 10 measurements (100 ms)
    change of acceleration orientation is detected as scalar multiplication of acc vectors < 0
    :param acc_data: data with accelerometer measures
    :param time: current time counter
    :param parameters: list of current parameters
    :param hit is True if hit started
    :return: 1 if hit else 0
    """
    change = 0
    for i in range(len(acc_data) - 2):
        mul = sum([acc_data[i][j] * acc_data[i + 2][j] for j in range(3)])
        if mul < -HIT_SCALAR_LEVEL:
            change += 1
        if change > 0 and hit == 0:
            print('HIT! at %i' % time)
            if time not in parameters['hit_starts']:
                parameters['hit_starts'].append(time)
            return True
    if change == 0:
        return False


def check_dynamic_swing(gyro_data, time, parameters, actions) -> bool:
    """
    function detects swing movement using
    :param gyro_data: gyroscope data
    :param time: current time
    :param parameters: list with parameters of system
    :param actions: list of actions
    :return: True if swing else False
    """
    w = sum([gyro_data[9][i] * gyro_data[9][i] for i in [1, 2]])
    # print("w = %f, started to rise = %i, is rising = %f" % (w, parameters['w_start'], parameters['w_rising']))
    if actions['swing']:
        if not actions['spin']:
            if parameters['swing_counter'] >= SPIN_COUNTER and parameters['w_swing_max'] > SPIN_W and time - \
                    parameters['swing_starts'][-1] > SWING_CIRCLE_TIME / sqrt(parameters['w_swing_max']):
                actions['spin'] = True
                parameters['spin_starts'].append(time)
                print("spin started at %i" % time)
                parameters['w_spin'] = w
        if actions['spin']:
            if w > parameters['w_spin']:
                parameters['w_spin'] = w
            if w < SPIN_LOW_W:
                actions['spin'] = False
                parameters['w_spin_prev'] = w
                parameters['swing_counter'] = 1
                parameters['swing_starts'].append(time)
                print("returned to swing %i" % time)
            if time - parameters['spin_starts'][-1] > SPIN_CIRCLE_TIME / sqrt(parameters['w_prev_spin']):
                print("one more spin at %i" % time)
                parameters['w_spin_prev'] = parameters['w_spin']
                parameters['w_spin'] = w
                parameters['spin_starts'].append(time)

        if not actions['spin']:
            if time - parameters['swing_starts'][-1] > SWING_CIRCLE_TIME / sqrt(parameters['w_swing_max']) and \
                            parameters['w_swing_max'] > SWING_CIRCLE_W:
                print("one_more_swing started at %i" % time)
                parameters['swing_starts'].append(time)
                parameters['swing_counter'] += 1
        if w > parameters['w_swing_max']:
            parameters['w_swing_max'] = w
        if parameters['w_rising'] == 0 and w < SWING_PROCENT * parameters['w_swing_max']:
            parameters['swing_stop'] += 1
            if parameters['swing_stop'] >= SWING_TIME_END:
                parameters['swing_stop'] = 0
                print('SWING ended at %i, w_level= %i' % (time, parameters['w_swing_max']))
                actions['spin'] = 0
                parameters['w_swing_max'] = SWING_LOW_W
                parameters['swing_counter'] = 0
                return False
        else:
            parameters['swing_stop'] = 0
        return True
    if not actions['swing']:
        parameters['swing_stop'] = 0
        if parameters['w_rising'] and (time - parameters['w_start']) > SWING_TIME and w > SWING_HIGH_W:
            # or (parameters['a_swing'] and (time - parameters['a_swing_start'] > SWING_TIME)):
            print('SWING started at %i' % time)
            parameters['w_start'] = 1
            parameters['swing_counter'] = 1
            if time not in parameters['swing_starts']:
                parameters['swing_starts'].append(time)
            return True
        return False


def check_new_swing(gyro_data, acc_data, time, parameters, actions) -> bool:
    """
    function detects swing. Swing is detected if angular velocity rises during last 10 measurements
    and angular acceleration     for this time is more then SWING_HIGH_W threshold
    :param gyro_data:  queue with last ten gyro measurements
    :param acc_data: queue with last ten acc measurements
    :param time: current time counter
    :param parameters: dict with parameteres
    :param actions: currents action states
    :return: 1 if swing else 0
    """
    if actions['swing']:
        change = 0
        mul = sum([acc_data[0][j] * acc_data[9][j] for j in range(3)])
        if mul < -400:
            change = 1
        # print(parameters['w_swing'])
        if (parameters['w_swing']) == 0:
            # and parameters['a_swing'] == 0) or change>0:
            parameters['swing_stop'] += 1
            if parameters['swing_stop'] >= 1:
                parameters['swing_stop'] = 0
                print('SWING ended at %i change: %i' % (time, change))
                actions['spin'] = 0
                return False
        else:
            parameters['swing_stop'] = 0
            # parameters['a_swing'] = 0
        return True
    if not actions['swing']:
        parameters['swing_stop'] = 0
        # div = sum(
        #    [(gyro_data[SWING_TIME - 1][i] - gyro_data[0][i]) * (gyro_data[SWING_TIME - 1][i] - gyro_data[0][i]) for i
        #     in [1, 2]])
        div = sum([gyro_data[0][i] * gyro_data[0][i] for i in [1, 2]])
        if (parameters['w_rising'] and (time - parameters['w_start']) > SWING_TIME and div > SWING_HIGH_W) or (
                    parameters['a_swing'] and (time - parameters['a_swing_start'] > SWING_TIME)):
            print('SWING started at %i' % time)
            parameters['w_start'] = 1
            if time not in parameters['swing_starts']:
                parameters['swing_starts'].append(time)
            return True
        return False


def check_swing(gyro_data, time, parameters) -> bool:
    """
    function detects swing. Swing is detected if angular velocity rises during last 10 measurements
    and angular acceleration     for this time is more then SWING_HIGH_W threshold
    :param gyro_data:  queue with last ten gyro measurements
    :param time: current time counter
    :param parameters: dict with parameteres
    :return: 1 if swing else 0
    """
    if parameters['w_rising'] and (time - parameters['w_start']) > SWING_TIME:
        # div = sum([(gyro_data[SWING_TIME-1][i] - gyro_data[0][i]) * (gyro_data[SWING_TIME-1][i] - gyro_data[0][i]) for i in [1, 2]])
        div = sqrt(gyro_data[SWING_TIME - 1][1] * gyro_data[SWING_TIME - 1][1] + gyro_data[SWING_TIME - 1][2] *
                   gyro_data[SWING_TIME - 1][2])
        div -= sqrt(gyro_data[0][1] * gyro_data[0][1] + gyro_data[0][2] * gyro_data[0][2])
        if div / SWING_TIME > SWING_HIGH_W:
            print('SWING started at %i' % parameters['w_start'])
            if not parameters['w_start'] in parameters['swing_starts']:
                parameters['swing_starts'].append(parameters['w_start'])
            return True
    return False


def check_stab(acc_data, time, parameters, stab) -> bool:
    """
    function detects stab action
    stab is action with high acceleration and low angular velocity
    :param acc_data: 10 last accelerometer measurements
    :param time: current time counter
    :param parameters: parameters of system
    :param stab: current state of stab
    :return: 1 is stab else 0
    """
    print(parameters['a_stab_start'], parameters['w_high_stab'], time)
    if (time - parameters['a_stab_start']) < STAB_TIME and (
                        time - parameters['w_high_stab'] > STAB_TIME or parameters['w_high_stab'] == -1):
        change = 0
        for i in range(min(STAB_TIME - 1, len(acc_data) - 1)):
            mul = sum([acc_data[9][j] * acc_data[9 - i][j] for j in range(3)])
            if mul < STAB_SCALAR_LEVEL:
                change += 1
            if change > 0 and stab == 0 and (
                        not parameters['stab_starts'] or time - parameters['stab_starts'][-1] > STAB_PAUSE):
                print('HIT! at %i' % time)
                if time not in parameters['stab_starts']:
                    parameters['stab_starts'].append(time)
                return True
        if change == 0:
            return False
    return False
