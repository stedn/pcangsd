"""
Call genotypes from posterior genotype probabilities using estimated individual allele frequencies as prior.
Can be performed with and without taking inbreeding into account.
"""

__author__ = "Jonas Meisner"

# Import libraries
import numpy as np
from numba import jit
import threading

##### Functions #####
# Genotype calling without inbreeding
@jit("void(f4[:, :], f4[:, :], f8, i8, i8, u1[:, :])", nopython=True, nogil=True, cache=True)
def gProbGeno(likeMatrix, indF, delta, S, N, G):
	m, n = likeMatrix.shape # Dimension of likelihood matrix
	m /= 3 # Number of individuals
	
	for ind in range(S, min(S+N, m)):
		# Estimate posterior probabilities
		probMatrix = np.empty((3, n), dtype=np.float32)
		for s in range(n):
			probMatrix[0, s] = likeMatrix[3*ind, s]*((1 - indF[ind, s])*(1 - indF[ind, s]))
			probMatrix[1, s] = likeMatrix[3*ind+1, s]*(2*indF[ind, s]*(1 - indF[ind, s]))
			probMatrix[2, s] = likeMatrix[3*ind+2, s]*(indF[ind, s]*indF[ind, s])
		probMatrix /= np.sum(probMatrix, axis=0)

		# Find genotypes with highest probability
		for s in range(n):
			geno = np.argmax(probMatrix[:, s])
			if probMatrix[geno, s] < delta:
				G[ind, s] = 9
			else:
				G[ind, s] = geno

# Genotype calling with inbreeding
@jit("void(f4[:, :], f4[:, :], f4[:], f8, i8, i8, u1[:, :])", nopython=True, nogil=True, cache=True)
def gProbGenoInbreeding(likeMatrix, indF, F, delta, S, N, G):
	m, n = likeMatrix.shape # Dimension of likelihood matrix
	m /= 3 # Number of individuals
	
	for ind in range(S, min(S+N, m)):
		# Estimate posterior probabilities
		probMatrix = np.empty((3, n), dtype=np.float32)
		for s in range(n):
			probMatrix[0, s] = likeMatrix[3*ind, s]*((1 - indF[ind, s])*(1 - indF[ind, s]) + indF[ind, s]*(1 - indF[ind, s])*F[ind])
			probMatrix[1, s] = likeMatrix[3*ind+1, s]*(2*indF[ind, s]*(1 - indF[ind, s])*(1 - F[ind]))
			probMatrix[2, s] = likeMatrix[3*ind+2, s]*(indF[ind, s]*indF[ind, s] + indF[ind, S]*(1 - indF[ind, S])*F[ind])
		probMatrix /= np.sum(probMatrix, axis=0)

		# Find genotypes with highest probability
		for s in range(n):
			geno = np.argmax(probMatrix[:, s])
			if probMatrix[geno, s] < delta:
				G[ind, s] = 9
			else:
				G[ind, s] = geno


##### Genotype calling #####
def callGeno(likeMatrix, indF, F=None, delta=0.0, threads=1):
	m, n = likeMatrix.shape # Dimension of likelihood matrix
	m /= 3 # Number of individuals
	chunk_N = int(np.ceil(float(m)/threads))
	chunks = [i * chunk_N for i in range(threads)]

	# Initiate genotype matrix
	G = np.empty((m, n), dtype=np.uint8)

	# Call genotypes with highest posterior probabilities
	if type(F) != type(None):
		# Multithreading
		threads = [threading.Thread(target=gProbGenoInbreeding, args=(likeMatrix, indF, F, delta, chunk, chunk_N, G)) for chunk in chunks]
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()
	else:
		# Multithreading
		threads = [threading.Thread(target=gProbGeno, args=(likeMatrix, indF, delta, chunk, chunk_N, G)) for chunk in chunks]
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()

	return G