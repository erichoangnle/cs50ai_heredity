import csv
import itertools
import sys

PROBS = {

    # Unconditional probabilities for having gene
    "gene": {
        2: 0.01,
        1: 0.03,
        0: 0.96
    },

    "trait": {

        # Probability of trait given two copies of gene
        2: {
            True: 0.65,
            False: 0.35
        },

        # Probability of trait given one copy of gene
        1: {
            True: 0.56,
            False: 0.44
        },

        # Probability of trait given no gene
        0: {
            True: 0.01,
            False: 0.99
        }
    },

    # Mutation probability
    "mutation": 0.01
}


def main():

    # Check for proper usage
    if len(sys.argv) != 2:
        sys.exit("Usage: python heredity.py data.csv")
    people = load_data(sys.argv[1])

    # Keep track of gene and trait probabilities for each person
    probabilities = {
        person: {
            "gene": {
                2: 0,
                1: 0,
                0: 0
            },
            "trait": {
                True: 0,
                False: 0
            }
        }
        for person in people
    }

    # Loop over all sets of people who might have the trait
    names = set(people)
    for have_trait in powerset(names):

        # Check if current set of people violates known information
        fails_evidence = any(
            (people[person]["trait"] is not None and
             people[person]["trait"] != (person in have_trait))
            for person in names
        )
        if fails_evidence:
            continue
        
        # Loop over all sets of people who might have the gene
        for one_gene in powerset(names):
            for two_genes in powerset(names - one_gene):

                # Update probabilities with new joint probability
                p = joint_probability(people, one_gene, two_genes, have_trait)
                update(probabilities, one_gene, two_genes, have_trait, p)

    # Ensure probabilities sum to 1
    normalize(probabilities)

    # Print results
    for person in people:
        print(f"{person}:")
        for field in probabilities[person]:
            print(f"  {field.capitalize()}:")
            for value in probabilities[person][field]:
                p = probabilities[person][field][value]
                print(f"    {value}: {p:.4f}")


def load_data(filename):
    """
    Load gene and trait data from a file into a dictionary.
    File assumed to be a CSV containing fields name, mother, father, trait.
    mother, father must both be blank, or both be valid names in the CSV.
    trait should be 0 or 1 if trait is known, blank otherwise.
    """
    data = dict()
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            data[name] = {
                "name": name,
                "mother": row["mother"] or None,
                "father": row["father"] or None,
                "trait": (True if row["trait"] == "1" else
                          False if row["trait"] == "0" else None)
            }
    return data


def powerset(s):
    """
    Return a list of all possible subsets of set s.
    """
    s = list(s)
    return [
        set(s) for s in itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    ]


def prob_table():
    """
    Return a probability distribution table for child gene.
    """
    parent = {
        0: 0.01,
        1: 0.50,
        2: 0.99
    }

    table = {}

    for mg in range(3):
        for fg in range(3):
            entry = {}
            a = (1 - parent[mg]) * (1 - parent[fg])
            b = (parent[mg] * (1 - parent[fg])) + ((1 - parent[mg]) * parent[fg])
            c = parent[mg] * parent[fg]
            entry[0] = a
            entry[1] = b
            entry[2] = c
            table[mg, fg] = entry

    return table



def joint_probability(people, one_gene, two_genes, have_trait):
    """
    Compute and return a joint probability.

    The probability returned should be the probability that
        * everyone in set `one_gene` has one copy of the gene, and
        * everyone in set `two_genes` has two copies of the gene, and
        * everyone not in `one_gene` or `two_gene` does not have the gene, and
        * everyone in set `have_trait` has the trait, and
        * everyone not in set` have_trait` does not have the trait.
    """
    # Get probability table for child gene
    table = prob_table()

    # Initialize joint probability
    joint_p = 1

    # Loop over all person in people
    for person, value in people.items():

        # If person is parent
        if value['mother'] is None and value['father'] is None:

            # Has trait
            if person in have_trait:
                if person in one_gene:
                    pg = PROBS['gene'][1]
                    pt = PROBS['trait'][1][True]
                elif person in two_genes:
                    pg = PROBS['gene'][2]
                    pt = PROBS['trait'][2][True]
                else:
                    pg = PROBS['gene'][0]
                    pt = PROBS['trait'][0][True]

            # Doesn't have trait
            else:
                if person in one_gene:
                    pg = PROBS['gene'][1]
                    pt = PROBS['trait'][1][False]
                elif person in two_genes:
                    pg = PROBS['gene'][2]
                    pt = PROBS['trait'][2][False]
                else:
                    pg = PROBS['gene'][0]
                    pt = PROBS['trait'][0][False]

        # If person is child
        else:

            # Get mother's number of copies
            if value['mother'] in one_gene:
                mg = 1
            elif value['mother'] in two_genes:
                mg = 2
            else:
                mg = 0
            
            # Get father's number of copies
            if value['father'] in one_gene:
                fg = 1
            elif value['father'] in two_genes:
                fg = 2
            else:
                fg = 0

            # Has trait
            if person in have_trait:
                if person in one_gene:
                    pt = PROBS['trait'][1][True]
                    pg = table[mg, fg][1]
                elif person in two_genes:
                    pt = PROBS['trait'][2][True]
                    pg = table[mg, fg][2]
                else:
                    pt = PROBS['trait'][0][True]
                    pg = table[mg, fg][0]

            # Doesn't have trait
            else:
                if person in one_gene:
                    pt = PROBS['trait'][1][False]
                    pg = table[mg, fg][1]
                elif person in two_genes:
                    pt = PROBS['trait'][2][False]
                    pg = table[mg, fg][2]
                else:
                    pt = PROBS['trait'][0][False]
                    pg = table[mg, fg][0]

        p = pt * pg
        joint_p *= p

    return joint_p


def update(probabilities, one_gene, two_genes, have_trait, p):
    """
    Add to `probabilities` a new joint probability `p`.
    Each person should have their "gene" and "trait" distributions updated.
    Which value for each distribution is updated depends on whether
    the person is in `have_gene` and `have_trait`, respectively.
    """
    # Loop over all person in probabilities
    for person in probabilities:
        
        # Has trait
        if person in have_trait:
            if person in one_gene:
                probabilities[person]['trait'][True] += p
                probabilities[person]['gene'][1] += p
            elif person in two_genes:
                probabilities[person]['trait'][True] += p
                probabilities[person]['gene'][2] += p
            else:
                probabilities[person]['trait'][True] += p
                probabilities[person]['gene'][0] += p
        
        # Doesn't have trait
        else:
            if person in one_gene:
                probabilities[person]['trait'][False] += p
                probabilities[person]['gene'][1] += p
            elif person in two_genes:
                probabilities[person]['trait'][False] += p
                probabilities[person]['gene'][2] += p
            else:
                probabilities[person]['trait'][False] += p
                probabilities[person]['gene'][0] += p

    return None


def normalize(probabilities):
    """
    Update `probabilities` such that each probability distribution
    is normalized (i.e., sums to 1, with relative proportions the same).
    """
    # Loop over all person in probabilities
    for person in probabilities:

        # Calculate scaling factor
        scale_gene = 1 / sum(list(probabilities[person]['gene'].values()))
        scale_trait = 1/ sum(list(probabilities[person]['trait'].values()))

        # Update values in gene
        for value in probabilities[person]['gene'].keys():
            probabilities[person]['gene'][value] *= scale_gene
        
        # Update values in trait
        for value in probabilities[person]['trait'].keys():
            probabilities[person]['trait'][value] *= scale_trait

    return None


if __name__ == "__main__":
    main()
