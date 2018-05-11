"""
Help functions to use in the PCAngsd framework.
"""

__author__ = "Jonas Meisner"

# Import libraries
import numpy as np
from numba import jit
from math import sqrt
from scipy.stats import binom
import threading

# Root mean squared error
@jit("f8(f8[:], f8[:])", nopython=True, nogil=True, cache=True)
def rmse1d(A, B):
	sumA = 0.0
	for i in range(A.shape[0]):
		sumA += (A[i] - B[i])*(A[i] - B[i])
	sumA /= (A.shape[0])
	return sqrt(sumA)

# Multi-threaded RMSE
@jit("void(f4[:, :], f4[:, :], i8, i8, f8[:])", nopython=True, nogil=True, cache=True)
def rmse2d_inner_float32(A, B, S, N, V):
	m, n = A.shape
	for i in range(S, min(S+N, m)):
		for j in range(n):
			V[i] += (A[i, j] - B[i, j])*(A[i, j] - B[i, j])

def rmse2d_multi_float32(A, B, chunks, chunk_N):
	m, n = A.shape
	sumA = np.zeros(m)

	# Multithreading
	threads = [threading.Thread(target=rmse2d_inner_float32, args=(A, B, chunk, chunk_N, sumA)) for chunk in chunks]
	for thread in threads:
		thread.start()
	for thread in threads:
		thread.join()

	return sqrt(np.sum(sumA)/(m*n))

@jit("void(f8[:, :], f8[:, :], i8, i8, f8[:])", nopython=True, nogil=True, cache=True)
def rmse2d_inner(A, B, S, N, V):
	m, n = A.shape
	for i in range(S, min(S+N, m)):
		for j in range(n):
			V[i] += (A[i, j] - B[i, j])*(A[i, j] - B[i, j])

def rmse2d_multi(A, B, chunks, chunk_N):
	m, n = A.shape
	sumA = np.zeros(m)

	# Multithreading
	threads = [threading.Thread(target=rmse2d_inner, args=(A, B, chunk, chunk_N, sumA)) for chunk in chunks]
	for thread in threads:
		thread.start()
	for thread in threads:
		thread.join()

	return sqrt(np.sum(sumA)/(m*n))

# Root mean squared error
@jit("f8(f8[:, :], f8[:, :])", nopython=True, nogil=True, cache=True)
def rmse2d(A, B):
	sumA = 0.0
	for i in range(A.shape[0]):
		for j in range(A.shape[1]):
			sumA += (A[i, j] - B[i, j])*(A[i, j] - B[i, j])
	sumA /= (A.shape[0]*A.shape[1])
	return sqrt(sumA)

# Multi-threaded frobenius
@jit("void(f4[:, :], f8[:, :], i8, i8, f8[:])", nopython=True, nogil=True, cache=True)
def frobenius2d_inner(A, B, S, N, V):
	m, n = A.shape
	for i in range(S, min(S+N, m)):
		for j in range(n):
			V[i] += (A[i, j] - B[i, j])*(A[i, j] - B[i, j])

def frobenius2d_multi(A, B, chunks, chunk_N):
	m, n = A.shape
	sumA = np.zeros(m)

	# Multithreading
	threads = [threading.Thread(target=frobenius2d_inner, args=(A, B, chunk, chunk_N, sumA)) for chunk in chunks]
	for thread in threads:
		thread.start()
	for thread in threads:
		thread.join()

	return sqrt(np.sum(sumA))

# Frobenius norm
@jit("f8(f8[:, :], f8[:, :])", nopython=True, nogil=True, cache=True)
def frobenius(A, B):
	sumA = 0.0
	for i in range(A.shape[0]):
		for j in range(A.shape[1]):
			sumA += (A[i, j] - B[i, j])*(A[i, j] - B[i, j])
	return sqrt(sumA)

# Frobenius norm of single matrix
@jit("f8(f8[:, :])", nopython=True, nogil=True, cache=True)
def frobeniusSingle(A):
	sumA = 0.0
	for i in range(A.shape[0]):
		for j in range(A.shape[1]):
			sumA += A[i, j]*A[i, j]
	return sqrt(sumA)

# Convert PLINK genotype matrix into genotype likelihoods
@jit("void(f4[:, :], f4[:, :], i8, i8, f8)", nopython=True, nogil=True, cache=True)
def convertPlink(likeMatrix, G, S, N, epsilon):
	m, n = G.shape # Dimension of genotype matrix
	for ind in range(S, min(S+N, m)):
		for s in range(n):
			if np.isnan(G[ind, s]):
				likeMatrix[3*ind, s] = 0.333333
				likeMatrix[3*ind + 1, s] = 0.333333
				likeMatrix[3*ind + 2, s] = 0.333333
			else:
				for g in range(3):
					if int(G[ind, s]) == g:
						likeMatrix[3*ind + g, s] = 1.0 - epsilon
					else:
						likeMatrix[3*ind + g, s] = epsilon/2.0