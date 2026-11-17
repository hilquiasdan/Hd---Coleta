"""Testes dos extratores com amostras locais. Rodar: python -m pytest testes -q"""
import os, sys, re
AQUI = os.path.dirname(__file__); sys.path.insert(0, os.path.join(AQUI, '..'))
import extrator, gabarito, classificador, banco
AM = os.path.join(AQUI, 'amostras')
def test_multipla_escolha_separa_80_questoes():
    import json
    pg = json.load(open(os.path.join(AM, 'me_real_paginas.json')))
    tipo, its, mx = extrator.itens('me_real', pg, 'FGV')
    assert tipo == 'multipla' and mx == 80 and sum(1 for i in its if len(i['alternativas']) == 5) >= 76
def test_hash_ignora_acento_espaco_maiuscula():
    assert banco.hash_q('Ação  PENAL é pública') == banco.hash_q('acao penal e publica')
def test_escolhe_versao_unica_e_rejeita_ambigua():
    nums = list(range(1, 21)); a = {n: 'ABCDE'[n % 5] for n in nums}; b = {n: 'ABCDE'[(n + 1) % 5] for n in nums}
    assert gabarito.escolhe('multipla', nums, 'x', '', [('TIPO 1', a, '')])[0] == a
    extrator.X['x'] = [{'w': 600, 'l': []}]
    assert gabarito.escolhe('multipla', nums, 'x', '', [('TIPO 1', a, ''), ('TIPO 2', b, '')])[0] is None
def test_classificador_reconhece_lep():
    it = {'enunciado': 'Segundo a Lei de Execução Penal, a remição pelo trabalho é de um dia de pena a cada três dias trabalhados.', 'alternativas': [], 'texto_base': '', 'comando': '', 'sec': ''}
    assert classificador.classifica(it) == 'Execução Penal'
