"""
==========================
ADDITIONAL FUNCTIONALITIES
==========================

This module exists to host code for functionalities and measures I have
developed and published during my research, which might be of interest for
some users and which do not fully fit in the original goals of GAlib,
intended as a library for the analysis of complex networks.
The module also includes my own adaptation into Python of third-party
functions and measures I needed for my research, or merely for comparison.


ESTIMATION OF EXPECTED CROSS-CORRELATION
========================================
TopologicalSimilarity
    Computes the expected cross-correlation matrix of a given network.
ExponentialMapping
    Computes the expected cross-correlation matrix of a given network.
CovarianceLinearGaussian
    Approximated covariance matrix of a system of Gaussian noise sources.

NETWORK (DYNAMICS) COMPLEXITY MEASURES
=======================================
FunctionalComplexity
    Calculates the functional complexity of a correlation(-like) matrix.
NeuralComplexity
    Calculates the neural complexity of a correlation(-like) matrix.
NeuralComplexity_Sampled
    Calculates the neural complexity of a correlation(-like) matrix (Faster).
"""

__author__ = "Gorka Zamora-Lopez"
__email__ = "galib@Zamora-Lopez.xyz"
__copyright__ = "Copyright 2013-2018"
__license__ = "GPL"
__update__="30/03/2018"

import numpy as np
import numpy.random
import scipy.linalg
import gatools


############################################################################
"""ESTIMATION OF EXPECTED CROSS-CORRELATION"""
def TopologicalSimilarity(adjmatrix, coupling):
    """Computes the expected cross-correlation matrix of a given network.

    This function estimates the expected correlations between its nodes that
    a dynamical process on the network tends to generate. The estimation assumes
    that the "influence" of one node over another distributes over all possible
    paths but that the influence decays along the paths. This decay is estimated
    as the communicability matrix. Pairwise correlation is assumed, according
    to the patterns of inputs two nodes tend to receive.
    See further details in our paper:
    "Bettinardi et al. Chaos 27:047409 (2017)"

    Parameters
    ----------
    adjmatrix : ndarray of rank-2
        The adjacency matrix of the network.
    coupling : real valued number
        The coupling strength of all connections.

    Returns
    -------
    corrmatrix : ndarray of rank-2, same size as adjmatrix.
        The correlation matrix of the expected functional connectivity.

    See Also
    --------
    ExponentialMapping : Expected cross-correlation matrix of a given network.
    CovarianceLinearGaussian : Covariance matrix of an Ornstein-Uhlenbeck process.
    """
    # 0) Security check on the dtype
    if adjmatrix.dtype not in ['float32','float64','float']:
        adjmatrix = adjmatrix.astype(np.float64)

    # 1) Compute the communicability matrix
    Cmatrix = scipy.linalg.expm(coupling*adjmatrix).T

    # 2) Compute the product between all columns (Cmatrix was transposed)
    #    and the normalization
    corrmatrix = np.inner(Cmatrix, Cmatrix)
    norms = scipy.linalg.norm(Cmatrix, axis=1)
    normmatrix = np.outer(norms, norms.T)

    corrmatrix = corrmatrix / normmatrix
    return corrmatrix

def ExponentialMapping(adjmatrix, coupling, partialcorr=False):
    """Computes the expected cross-correlation matrix of a given network.

    This function estimates the expected cross-correlation matrix of a dynamical
    process on a network, assuming that each node is a linear Gaussian noise
    source and that the "influence" of one node over another distributes over
    all possible paths but that the influence decays along the paths. This decay
    is estimated as the communicability matrix. See further details in our paper:
    "Zamora-Lopez et al. Sci. Reps. 6:38424 (2016)."

    NOTE: The output of the Exponential Mapping is numerically the same as the
    output of the Topological Similarity measure, when the noise level for all
    nodes is the same, and when the decay rate for all nodes is the same, as
    shown in "Bettinardi et al. Chaos 27:047409 (2017) (Supp. Material)."
    I recommend to use TopologicalSimilarity() instead. I added this function
    here only for reference from interested readers of the paper above.

    Parameters
    ----------
    adjmatrix : ndarray of rank-2
        The adjacency matrix of the network.
    coupling : real valued number
        The coupling strength of all connections.
    partialcorr : boolean (optional)
        If 'True', the function returs the partial correlation matrix.

    Returns
    -------
    corrmatrix : ndarray of rank-2, same size as adjmatrix.
        The correlation matrix of the expected functional connectivity.

    See Also
    --------
    TopologicalSimilarity : Expected cross-correlation matrix of a given network.
    CovarianceLinearGaussian : Covariance matrix of an Ornstein-Uhlenbeck process.
    """
    # 0) Security check on the dtype
    if adjmatrix.dtype not in ['float32','float64','float']:
        adjmatrix = adjmatrix.astype(np.float64)

    # 1) Compute the node-to-node influence
    Qmatrix = scipy.linalg.expm(coupling*adjmatrix)
    # 2) Normalize the Qmatrix to avoid numerical overload
    maxQvalue = max( abs(Qmatrix.min()), abs(Qmatrix.max()) )

    if partialcorr:
        #Qmatrix = Qmatrix / maxQvalue
        # 3) Compute the covariance matrix and its inverse
        covmatrix = np.dot(Qmatrix.T, Qmatrix)
        covmatrix = scipy.linalg.inv(covmatrix)
        # 4) Convert to a correlation matrix and return
        diagvalues = np.diag(covmatrix)
        normmatrix = np.sqrt( np.outer(diagvalues,diagvalues) )
        corrmatrix = - covmatrix / normmatrix

    else:
        Qmatrix = Qmatrix / maxQvalue
        # 3) Compute the covariance matrix
        covmatrix = np.dot(Qmatrix.T, Qmatrix)
        # 4) Convert to a correlation matrix and return
        diagvalues = np.diag(covmatrix)
        normmatrix = np.sqrt( np.outer(diagvalues,diagvalues) )
        corrmatrix = covmatrix / normmatrix

    return corrmatrix

def CovarianceLinearGaussian(adjmatrix, coupling, noiselevel=1.0, noisearray=[]):
    """Estimates the covariance matrix of a system of Gaussian noise sources.

    This function returns an analytical approximation of the time-average
    covariance matrix of a system of linearly coupled Gaussian noise sources.
    Each node of the system (network) is described as fixed point which receives
    a Gaussian noise and the input from its neighbours. Given that X is the
    vector of states of the nodes and A is the adjacency matrix of the
    connectivity and 'g' a global coupling strength applied to all links, the
    equation of motion of the system is approximately:
        Xdot = -a*X + g* A*X + D*noise
    where 'a' is the decay rate parameter and D is the intensity of the Gaussian
    white noise of variance = 1.
    This model has received many different names. It is often refered as the
    Ornstein-Uhlenbeck process, the continous version of a discrete-time
    autorregressive model.

    The analytical approximation in this function is coded to match the
    description given in:
        "Tononi et al. PNAS 91, 5033-5037 (1994)"
    which has been often used in the neuroscience / brain connectivity
    literature.

    - NOTE 1: Because this model diverges when g equals the largest eigenvalue
    of the adjacency matrix, it is highly recommended to provide as input the
    normalised version of the adjacency matrix. That is, the adjacency
    matrix divided by its spectral diameter. In that case, 'g' takes values
    between 0 and 1. See "Zamora-Lopez et al. Front. Neuroinform. 4, (2010)".

    - NOTE 2: In case the network is directed, the covariance matrix is
    computed out of the transposed adjacency matrix, such that the dynamics of
    a node is governed by the inputs i receives, instead of by its outputs.

    Parameters
    ----------
    adjmatrix : ndarray of rank-2
        The adjacency matrix of the network. It can be either weighted or
        binary, directed or undirected. It is recommended to provide the
        adjacency matrix normalised by its largest eigenvalue (or spectral
        diameter).
    coupling : real valued number
        The coupling strength of all connections. 'coupling' should be smaller
        than the spectral diameter of 'adjmatrix'. If this has been already
        normalised, then g can take values between 0 and 1.
    noiselevel : real valued number (optional)
        The intensity of the noise, if all nodes should receive the same.
    noisearray : list, tuple or array_like (optional)
        An array contaning the individual noise level each node receives.
        If left empy, all nodes will receive the same noise level given by
        parameter 'noiselevel'. Else, 'noiselevel' will be replaced by the
        'noisearray' parameter. The length of 'noisearray' must be the number
        of nodes in the network.

    Returns
    -------
    COVmatrix : ndarray of rank-2
        The approximated time-average covariance matrix of the system.

    See Also
    --------
    TopologicalSimilarity : Expected cross-correlation matrix of a given network.
    ExponentialMapping : Expected cross-correlation matrix of a given network.
    """
    # 0) Security checks and preparations
    if adjmatrix.dtype not in ['float32', 'float64']:
        adjmatrix = adjmatrix.astype(np.float64)

    # 1) Construct the uncorrelated noise vector (diagonal matrix)
    N = len(adjmatrix)
    if len(noisearray) > 0:
        assert len(noisearray) == N, "'noisearray' not aligned with 'adjmatrix'"
        R = np.array(noisearray, np.float64) * np.identity(N).astype(np.float64)
    else:
        R = noiselevel * np.identity(N).astype(np.float64)

    # 2.2) Compute the Q matrix
    Qmatrix = scipy.linalg.inv(np.identity(N,np.float64) - coupling*adjmatrix)
    Qt = Qmatrix.T

    # 2.3) Compute the covariance matrix
    COVmatrix = np.dot(Qt,R**2)
    COVmatrix = np.dot(COVmatrix,Qmatrix)

    return COVmatrix

def Covmat2Corrmat(covmatrix):
    """Normalises a covariance matrix into a cross-correlation matrix.

    Parameters
    ----------
    covmatrix : ndarray of rank-2
        A covariance matrix.

    Returns
    -------
    corrmatrix : ndarray of rank-2
        The cross-correlation matrix.
    """
    # 0) Prepare for calculation
    if covmatrix.dtype not in ['float32','float64','float']:
        covmatrix = covmatrix.astype(np.float)

    # 1) Calculate the normalization factor for each pair
    diagvalues = np.diag(covmatrix).astype(np.float)
    normmatrix = np.sqrt(np.outer(diagvalues,diagvalues))

    # 2) Return result
    corrmatrix = covmatrix / normmatrix
    return corrmatrix


############################################################################
"""NETWORK (DYNAMICS) COMPLEXITY MEASURES"""
def FunctionalComplexity(corrmatrix, nbins=50, datarange=[0,1]):
    """Calculates the functional complexity of a correlation(-like) matrix.

    Given the cross-correlation matrix out of some network dynamics or an
    arbitrary multivariate dynamical system, this function computes the
    functional complexity of the system. Functional complexity takes value 0 if
    the elements or nodes are (dynamically or statistically) independent of
    each other. It takes value 1 when the elements or nodes are all fully
    correlated with each other. See definition, details and comparison
    to other measures in our paper:
    "Zamora-Lopez et al. Sci. Reps. 6:38424 (2016)."

    NOTE: Functional complexity can be estimated out of any matrix of pair-wise
    statistical associations between the elements of a network or multi-
    variate (dynamical or stochastic) system, e.g. the matrix of pairwise
    mutual information values. The range of accepted values may have to be
    adapted.

    Parameters
    ----------
    corrmatrix : ndarray of rank-2.
        The correlation or pair-wise statistical association matrix.
    nbins : integer (optional)
        Number of bins for which the distribution of values in the matrix shall
        be estimated.
    datarange : list, tuple or array_like (optional)
        A sequence of length = 2 containing the smallest and the largest values
        expected in the statistical association matrix.

    Returns
    -------
    fcomplexity : real valued number
        The functional complexity, ranging from 0 to 1.

    See Also
    --------
    NeuralComplexity : Measure of complexity by Tononi, Sporns and Edelmann.
    NeuralComplexity_Sampled : Measure of complexity by Tononi, Sporns et al.
    """
    # 0) Security checks
    assert len(np.shape(corrmatrix)) == 2, \
        'Input data not a correlation matrix. Data not alligned.'
    assert corrmatrix.min() >= datarange[0], \
        'Input data not in range. Values smaller than range found.'
    assert corrmatrix.max() <= datarange[1], \
        'Input data not in range. Values larger than range found.'

    # 1) Use only the upper triangular values of the correlation matrix
    N = len(corrmatrix)
    idx = np.triu_indices(N,1)
    corrvalues = corrmatrix[idx]

    # 2) Compute the distribution of the correlation values
    # Convert corrvalues to 'float32' to avoid numerical issues. Don't ask me why.
    ydata, xdata = np.histogram(corrvalues.astype(np.float32), nbins, datarange, density=True)
    # Normalize probability. histogram() does not properly normalize.
    ydata /= ydata.sum()

    # 3) Compute functional complexity
    normfactor = 0.5 * float(nbins) / (nbins-1)
    uniformdistrib = 1./nbins * np.ones(nbins, np.float)
    fcomplexity = 1. - normfactor * np.add.reduce(abs(ydata - uniformdistrib))
    # fcomplexity = 1. - normfactor * (abs(ydata - uniformdistrib)).sum()

    # Clean some trash
    del xdata, corrvalues, uniformdistrib

    return fcomplexity

def NeuralComplexity(corrmatrix, bipartitions=None):
    """Calculates the neural complexity of a correlation(-like) matrix.

    This function calculates the 'neural complexity' measure proposed in
        "Tononi et al. PNAS 91, 5033-5037 (1994)"

    Parameters
    ----------
    corrmatrix : ndarray of rank-2.
        The correlation or pair-wise statistical association matrix.
    bipartitions : list
        A list of bipartitions of the nodes, e.g., [(1,2,3,4), (5,6)].

    Returns
    -------
    ncomplexity : real valued number
        The neural complexity value.

    See Also
    --------
    FunctionalComplexity : Functional complexity of a correlation(-like) matrix
    """
    # 0) Get ready for the calculations
    N = len(corrmatrix)

    # Find all possible bipartitions in a set of N nodes
    if not bipartitions:
        bipartitions = gatools.AllBipartitions(np.arange(N))

    nmax = N / 2
    detcorrmat = scipy.linalg.det(corrmatrix)

    # 1) Calculate the mutual information, for all bipartitions of all sizes
    counter = 0
    avmibips = np.zeros(nmax+1, np.float64)
    for n in xrange(1,nmax+1):
        # Number of bipartitions for set of size n and (N-n)
        nbips = gatools.Factorial(N) / (gatools.Factorial(n) * gatools.Factorial(N-n))

        # Correct nbips if N is even and if nbips = nmax
        if n == nmax and 2*n == N:
            nbips /= 2

        # Calculate mutual information for all bipartitions of sizes n, (N-n)
        mibips = np.zeros(nbips, np.float64)
        for i in xrange(nbips):
            # Choose a bipartition
            set1, set2 = bipartitions[counter+i]

            # Extract the submatrices for each bipartition
            submat1 = gatools.ExtractSubmatrix(corrmatrix, set1)
            submat2 = gatools.ExtractSubmatrix(corrmatrix, set2)

            # Compute the determinant of the submatrices
            detsubmat1 = scipy.linalg.det(submat1)
            detsubmat2 = scipy.linalg.det(submat2)

            # Compute the mutual information of the bipartition
            mibips[i] = 0.5 * ( np.log(detsubmat1) + np.log(detsubmat2) - np.log(detcorrmat) )

        counter += nbips

        # Average MI for all bipartitions of the same size
        avmibips[n] = mibips.mean()

    ncomplexity = avmibips.sum()
    return ncomplexity

def NeuralComplexity_Sampled(corrmatrix, maxiter=1000):
    """Calculates the neural complexity of a correlation(-like) matrix.

    This function calculates the 'neural complexity' measure proposed in
        "Tononi et al. PNAS 91, 5033-5037 (1994)"
    The difference with function 'NeuralComplexity()' is that the latter
    exhaustively computes the mutual information for all existing bipartitions
    of nodes in the network, which is computationally prohibitive for networks
    larger than N = 30 nodes. In this case, the calculation is limited to a
    a limited number of bipartitions (maxiter) among all possible. The
    sample bipartitions are generated at random.

    Parameters
    ----------
    corrmatrix : ndarray of rank-2.
        The correlation or pair-wise statistical association matrix.
    maxiter : integer
        Maximum number of bipartitions to generate for each size n, (N-n).

    Returns
    -------
    ncomplexity : real valued number
        The neural complexity value.

    See Also
    --------
    FunctionalComplexity : Functional complexity of a correlation(-like) matrix
    """
    # 0) GET READY FOR THE CALCULATIONS
    N = len(corrmatrix)

    nmax = N / 2
    detcorrmat = scipy.linalg.det(corrmatrix)
    factorialN = gatools.Factorial(N)
    nodelist = np.arange(N)

    # 1) Calculate the mutual information, for all bipartitions of all sizes
    avmibips = np.zeros(nmax+1, np.float64)
    for n in xrange(1,nmax+1):
        nbips = factorialN / (gatools.Factorial(n) * gatools.Factorial(N-n))

        # Correct nbips is N is even and if nbips = nmax
        if n == nmax and 2*n == N:
            nbips /= 2

        # Average of all bipartitions of size n, if nbips is small
        if nbips <= maxiter:
            mibips = np.zeros(nbips, np.float64)
            # Create all the bipartitions of size n
            bipartitions = gatools.AllBipartitions(nodelist, n)
            for i in xrange(nbips):
                # Choose a bipartition
                set1, set2 = bipartitions[i]

                # Extract the submatrices for each bipartition
                submat1 = gatools.ExtractSubmatrix(corrmatrix, set1)
                submat2 = gatools.ExtractSubmatrix(corrmatrix, set2)

                # Compute the determinant of the submatrices
                detsubmat1 = scipy.linalg.det(submat1)
                detsubmat2 = scipy.linalg.det(submat2)

                # Compute the mutual information of the bipartition
                mibips[i] = 0.5 * ( np.log(detsubmat1) + np.log(detsubmat2) - np.log(detcorrmat) )

        # If nbips is large, the average of randomly sampled bipartitions
        else:
            # print 'Sampling... n:', n
            mibips = np.zeros(maxiter, np.float64)
            for i in xrange(maxiter):
                # Generate a random bipartition of sizes n and N-n
                numpy.random.shuffle(nodelist)
                set1 = nodelist[:n]
                set2 = nodelist[n:]

                # Extract the submatrices for each bipartition
                submat1 = gatools.ExtractSubmatrix(corrmatrix, set1)
                submat2 = gatools.ExtractSubmatrix(corrmatrix, set2)

                # Compute the determinant of the submatrices
                detsubmat1 = scipy.linalg.det(submat1)
                detsubmat2 = scipy.linalg.det(submat2)

                # Compute the mutual information of the bipartition
                mibips[i] = 0.5 * ( np.log(detsubmat1) + np.log(detsubmat2) - np.log(detcorrmat) )

        # Average MI for all bipartitions of the same size
        avmibips[n] = mibips.mean()

    ncomplexity = avmibips.sum()
    return ncomplexity


#
