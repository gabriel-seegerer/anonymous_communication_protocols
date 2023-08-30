from p2p_network.amdc_for_p2p import find_d_and_gamma


if __name__ == "__main__":
    m_len = int(input("Input message length: "))
    # sec = int(input("Input security: "))
    sec = [i for i in range(1, 16)]
    print(f"m_len sec m'_len")
    for s in sec:
        d, gamma = find_d_and_gamma(s, m_len, False)
        print(f"{m_len:3d}  {s:2d}  {d * gamma + 2 * gamma:4d}")
