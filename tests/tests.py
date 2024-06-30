if __name__ == '__main__':
    
    import matplotlib.pyplot as plt 

    #with h5py.File('/home/alex/mnt/Data1/' 
    #    'ESRF/hc5078_10_13-02-2023-CDMX18/CDMX18/hc5078_CDMX18.h5', 'r') as file:
#
    #    g = file['CDMX18_rampe01_14.1']
    #    print(g)
#
    #    data = get_data_from_h5group(g)
    #    print(data)
#
    #    test = BlackBodySpec('test', **data)
    #    test.set_pars(dict(usebg=None, delta=113, lowerb=570, upperb = 920))
#
    #    print(test.time)
#
    #    test.eval_twocolor()
    #    test.eval_planck_fit()
    #    test.eval_wien_fit()
#
    #    plt.figure(1)
    #    plt.plot(test.lam, test.planck)
    #    plt.plot(test.lam[test.ind_interval], test.planck_fit)
    #    
    #    plt.figure(2)
    #    plt.plot(1/test.lam, test.wien)
    #    plt.plot(1/test.lam[test.ind_interval], test.wien_fit)
    #    
    #    plt.figure(3)
    #    plt.plot(test.lam[test.ind_interval][:-test.pars['delta']], test.twocolor)
#
    #    print(test.T_planck)
    #    print(test.T_wien)
    #    print(test.T_twocolor)
    #    print(test.T_std_twocolor)
#
    #    plt.show()
    with h5py.File('/home/alex/mnt/Data1/' 
        'ESRF/hc5078_10_13-02-2023-CDMX18/CDMX18/hc5078_CDMX18.h5', 'r') as file:
        g = file['CDMX18_mesh_HT_1.1']
        print(g)

        data = get_data_from_h5group(g)
        print(data[3])