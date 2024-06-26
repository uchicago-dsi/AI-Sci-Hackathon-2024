import sys
import rdkit
from rdkit import Chem
import dataclasses
import networkx as nx
import numpy as np

import bigsmiles_gen

# from util import get_smiles, SEED
import helper
import make_permutation

def make_graph_from_smiles(smi):
    big_mol = bigsmiles_gen.Molecule(smi)
    gen_mol = big_mol.generate()
    ffparam, mol = gen_mol.forcefield_types

    graph = nx.Graph()
    for atomnum in ffparam:
        atom = mol.GetAtomWithIdx(atomnum)
        graph.add_node(atomnum, atomic=atom.GetAtomicNum(),
                       valence=atom.GetTotalValence(),
                       formal_charge=atom.GetFormalCharge(),
                       aromatic=atom.GetIsAromatic(),
                       hybridization=int(atom.GetHybridization()),
                       radical_electrons=int(atom.GetNumRadicalElectrons()),
                       param=dataclasses.asdict(ffparam[atomnum]))
    for node in graph.nodes():
        atom = mol.GetAtomWithIdx(node)
        for bond in atom.GetBonds():
            graph.add_edge(int(bond.GetBeginAtomIdx()), int(bond.GetEndAtomIdx()),
                           type=int(bond.GetBondType()),
                           stereo=int(bond.GetStereo()),
                           aromatic=bond.GetIsAromatic(),
                           conjugated=bond.GetIsConjugated(),
                           )

    return graph

def prepare_sets(data_size:int, competition_size:int, seed:int, max_node_size:int=100):
    all_smi = []
    all_graphs = []
    smi_gen = get_smiles()
    while len(all_smi) < data_size + competition_size:
        smi = next(smi_gen)
        try:
            graph = make_graph_from_smiles(smi)
        except RuntimeError as exc:
            print(len(all_smi)/(data_size + competition_size), exc)
        except ValueError as exc:
            print(len(all_smi)/(data_size + competition_size), exc)
        except bigsmiles_gen.forcefield_helper.FfAssignmentError as exc:
            print(len(all_smi)/(data_size + competition_size), exc)
        else:
            if len(graph) < max_node_size:
                all_smi += [smi]
                all_graphs += [graph]

    rng = np.random.default_rng(seed=seed)
    idx = list(range(len(all_smi)))
    rng.shuffle(idx)

    shuffled_smi = [all_smi[i] for i in idx]
    shuffled_graphs = [all_graphs[i] for i in idx]

    data_smi = shuffled_smi[:data_size]
    data_graphs = shuffled_graphs[:data_size]

    competition_smi = shuffled_smi[data_size:]
    competition_graphs = shuffled_graphs[data_size:]

    return (data_smi, data_graphs), (competition_smi, competition_graphs)

def write_data(all_smi, all_graphs, name):
    dictionary = {}
    for smi, graph in zip(all_smi, all_graphs):
        dictionary[smi] = graph

    helper.write_data_to_json_file(dictionary, f"{name}.json")


def josh_set():
    smiles =    [
        "C1CC1",
        "C1OC1",
        "C1NC1",
        "CCCC(=O)C",
        "CCC(=O)CC",
        "CCCCC=O",
        "CCCC(=O)O",
        "CCOC(=O)C",
        "CC(=O)OC(=O)C",
        "CCNC(=O)C",
        "CCCC(=O)N",
        "C1=CC=CC=C1",
        "C1=CNC=C1",
        "C1=CNN=C1",
        "C1=CN=CN1",
        "C1=CSC=N1",
        "C1=COC=C1",
        "C1=CC=C2C(=C1)C=CN2",
        "C1=CC=C2C(=C1)C=CC=N2",
        "C1=C2C(=NC=N1)N=CN2",
    ]
    josh_graphs = {}
    for smi in smiles:
        try:
            graph = make_graph_from_smiles(smi)

        except RuntimeError as exc:
            print(smi, ecx)
        except ValueError as exc:
            print(smi, exc)
        except bigsmiles_gen.forcefield_helper.FfAssignmentError as exc:
            print(smi, exc)
        else:
            josh_graphs[smi] = graph

    helper.write_data_to_json_file(josh_graphs, "josh_set.json", indent=2)
    for smi in josh_graphs:
        g = josh_graphs[smi]
        make_permutation.remove_param(g)
    helper.write_data_to_json_file(josh_graphs, "josh_masked.json", indent=2)


def main(argv):
    if len(argv) != 0:
        raise RuntimeError("Specify exactly one SMILES string")

    # (data_smi, data_graphs), (competition_smi, competition_graphs) = prepare_sets(3000, 500, SEED)

    # write_data(data_smi, data_graphs, "data")
    # write_data(competition_smi, competition_graphs, "competition")

    josh_set()

if __name__ == "__main__":
    main(sys.argv[1:])
