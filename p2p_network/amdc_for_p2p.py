"""
Implementation of an AMDC protocol
For more see: "Supplemental Information: Experimental implementation of secure anonymous protocols on an eight-user
quantum network" - Huang, Joshi 2002
"""

import numpy as np
import yaml
from secrets import randbits
import galois


def debug_print(message, debug: bool) -> None:
    if debug is True:
        print(f"      {message}")


def find_d_and_gamma(beta: int, m_len: int, debug: bool) -> tuple[int, int]:
    """
    Finds d and gamma parameter based on beta and message length
    :param debug: if True, prints out calculation steps
    :param beta: security parameter
    :param m_len: length of message
    :return: d and gamma as tuple
    """
    d = 1
    while d * (beta + np.log2(d + 1)) < m_len:
        debug_print(f"Finding d: Trying d = {d}: result: {d * (beta + np.log2(d + 1)):.2f} - m_len = {m_len}",
                    debug)
        d += 2
    debug_print(f"Found d = {d}: result: {d * (beta + np.log2(d + 1)):.2f} - m_len = {m_len}", debug)
    gamma = int(np.ceil(beta + np.log2(d + 1)))
    return d, gamma


def get_binary_irreducible(gamma: int) -> str:
    """
    Gets irreducible binary polynomial of degree *gamma* from the .yaml file
    :param gamma: gamma parameter
    :return: String of 0's and 1's which represent a binary irreducible polynomial of degree gamma
    """
    with open("binary_irreducible_polynomials_dict.yaml", "r") as handle:
        irreducible_binary_polynomial_dict = yaml.safe_load(handle)
    return irreducible_binary_polynomial_dict.get(gamma)


def amdc_encode_message(message: list, beta: int, debug: bool) -> list[int]:
    """
    Encodes a message with an AMDC
    :param message: message as a field of 0's and 1's
    :param beta: probability that error is detected is 1-2**-beta
    :param debug: if True prints out calculation steps
    :return: encoded message as list of 0's and 1's
    """
    debug_print("----------Encoding with AMDC----------", debug)
    d, gamma = find_d_and_gamma(beta, len(message), debug)
    debug_print(f"d = {d}, gamma = {gamma}", debug)

    theta_binary = [randbits(1) for _ in range(gamma)]
    debug_print("Creating random theta binary string", debug)
    debug_print(f"theta_binary = {theta_binary} - len: {len(theta_binary)}", debug)

    debug_print(f"message: {message}", debug)
    # Fill message with 0 till length is d * gamma
    debug_print(f"0's appended: {d * gamma - len(message)}", debug)
    padded_message = message + [0] * (d * gamma - len(message))
    debug_print(f"Padded message: m = {padded_message} - len: {len(padded_message)}", debug)

    # Get irreducible polynomial from list
    b = get_binary_irreducible(gamma)
    debug_print(f"Get b from dict: {b}", debug)
    b_binary = [int(d) for d in str(b)]

    # Create polynomials
    debug_print("Creating polynomials", debug)
    gf = galois.GF(2)
    b_poly = galois.Poly(b_binary, gf)
    debug_print(f"b_poly = {b_poly}", debug)
    theta_poly = galois.Poly(theta_binary, gf)
    debug_print(f"theta_poly = {theta_poly}", debug)
    u_poly_list = [galois.Poly(u, gf) for u in np.array_split(padded_message, d)]
    debug_print(f"u_poly_list = {u_poly_list}", debug)
    for u in u_poly_list:
        debug_print(f"   u{u_poly_list.index(u)} = {u}", debug)

    # Calculate f(x)
    debug_print(f"Calculating f(x)", debug)
    f_poly = theta_poly ** (d + 2)
    for i in range(1, d + 1):
        f_poly += u_poly_list[i - 1] * (theta_poly ** i)

    debug_print(f"   f(x) = \n{f_poly}", debug)

    # Divide f(x)/b(x)
    quotient_poly = f_poly // b_poly
    remainder_poly = f_poly % b_poly
    debug_print("Calculate f(x)/b(x)", debug)
    debug_print(f"quotient = {quotient_poly}\nremainder = {remainder_poly}", debug)

    # cast np array to int_list, do modulo 2 and fill it with leading 0
    tau_binary = list(map(int, bin(remainder_poly)[2:]))
    tau_binary = [0] * (gamma - len(tau_binary)) + tau_binary
    debug_print(f"tau: {tau_binary} - len: {len(tau_binary)}", debug)

    # m' is m + theta + tau
    new_m = padded_message + theta_binary + tau_binary
    debug_print(f"\nm': {new_m}", debug)
    return new_m


def amdc_decode_message(encoded_message: list, message_length: int, beta: int, debug: bool) -> tuple[bool, list[int]]:
    """
    Decodes a message with AMDC
    :param encoded_message: encoded message as list of 0's and 1's
    :param message_length: length of the original message
    :param beta: beta parameter
    :param debug: if True, prints out steps
    :return: bool message is correct True or False, list of decoded message
    """
    debug_print("----------DECODING AMDC----------", debug)
    d, gamma = find_d_and_gamma(beta, message_length, debug)
    debug_print(f"d = {d}, gamma = {gamma}", debug)

    padded_message = encoded_message[:-2 * gamma]
    theta_binary = encoded_message[-2 * gamma: -gamma]
    tau_binary_received = encoded_message[-gamma:]

    debug_print(f"Received message = {padded_message}", debug)
    debug_print(f"Received theta_binary = {theta_binary}", debug)
    debug_print(f"Received tau_binary = {tau_binary_received}", debug)

    # Get irreducible polynomial from list
    b = get_binary_irreducible(gamma)
    debug_print(f"Get b from dict: {b}", debug)
    b_binary = [int(d) for d in str(b)]

    # Create polynomials
    debug_print("Creating polynomials", debug)
    gf = galois.GF(2)
    b_poly = galois.Poly(b_binary, gf)
    debug_print(f"b_poly = {b_poly}", debug)
    theta_poly = galois.Poly(theta_binary, gf)
    debug_print(f"theta_poly = {theta_poly}", debug)
    u_poly_list = [galois.Poly(u, gf) for u in np.array_split(padded_message, d)]
    debug_print(f"u_poly_list = {u_poly_list}", debug)
    for u in u_poly_list:
        debug_print(f"   u{u_poly_list.index(u)} = {u}", debug)

    # Calculate f(x)
    debug_print(f"Calculating f(x)", debug)
    f_poly = theta_poly ** (d + 2)
    for i in range(1, d + 1):
        f_poly += u_poly_list[i - 1] * (theta_poly ** i)

    debug_print(f"   f(x) = \n{f_poly}", debug)

    # Divide f(x)/b(x)
    quotient_poly = f_poly // b_poly
    remainder_poly = f_poly % b_poly
    debug_print("Calculate f(x)/b(x)", debug)
    debug_print(f"quotient = {quotient_poly}\nremainder = {remainder_poly}", debug)

    # cast np array to int_list, do modulo 2 and fill it with leading 0
    tau_binary_calculated = list(map(int, bin(remainder_poly)[2:]))
    tau_binary_calculated = [0] * (gamma - len(tau_binary_calculated)) + tau_binary_calculated
    debug_print(f"\ntau_calculated: {tau_binary_calculated} - len: {len(tau_binary_calculated)}", debug)
    debug_print(f"\ntau_received:   {tau_binary_received} - len: {len(tau_binary_received)}", debug)

    if tau_binary_calculated == tau_binary_received:
        message_correct = True
    else:
        message_correct = False
    return message_correct, padded_message[:message_length]
