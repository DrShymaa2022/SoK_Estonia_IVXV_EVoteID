//copilot wrapped run
import hashlib
from sympy import symbols, interpolate
from py_ecc.optimized_bls12_381 import curve_order, G1, multiply, add, Z1

# ----- Setup Functions -----
def trusted_setup(degree):
    r = 7  # fixed scalar for deterministic setup
    return [multiply(G1, pow(r, i, curve_order)) for i in range(degree + 1)]

def hash_vote(vote_data):
    h = hashlib.sha256(vote_data.encode()).hexdigest()
    return int(h, 16) % curve_order

def commit_polynomial(coeffs, setup):
    return sum([multiply(setup[i], coeff) for i, coeff in enumerate(coeffs)], Z1)

# ----- Verkle Tree CLI Class -----
class VerkleCLI:
    def __init__(self, max_degree=10):
        self.setup = trusted_setup(max_degree)
        self.votes_all = []
        self.votes_final = {}
        self.votes_multiple = {}

    def cast_vote(self, voter_id, vote_choice):
        h = hash_vote(vote_choice)
        self.votes_all.append((voter_id, h))
        if voter_id in self.votes_final:
            self.votes_multiple.setdefault(voter_id, []).append(self.votes_final[voter_id])
        self.votes_final[voter_id] = h
        print(f"\n🗳️ Voter {voter_id} cast vote: '{vote_choice}' (Hash: {h})")

    def generate_commitment(self, label, vote_list):
        x = symbols('x')
        points = [(i, vote_hash) for i, (_, vote_hash) in enumerate(vote_list)]
        poly = interpolate(points or [(0, 0)], x)
        coeffs = [int(c) % curve_order for c in poly.all_coeffs()]
        return commit_polynomial(coeffs, self.setup)

    def summarize(self):
        print("\n📦 Verkle Tree Commitments:")
        vt1 = self.generate_commitment("VT1", self.votes_all)
        print("🔗 VT₁ (All votes):", vt1)

        final_votes = list(self.votes_final.items())
        vt2 = self.generate_commitment("VT2", final_votes)
        print("🔗 VT₂ (Final votes):", vt2)

        duplicate_flat = [(vid, h) for vid, hs in self.votes_multiple.items() for h in hs]
        vt3 = self.generate_commitment("VT3", duplicate_flat)
        print("🔗 VT₃ (Duplicate votes):", vt3)

# ----- Run CLI -----
def run_cli():
    tree = VerkleCLI()
    print("🌿 Verkle Voting CLI\nCast your votes! Type 'done' when finished.")
    while True:
        voter = input("\nEnter voter ID (or 'done'): ").strip()
        if voter.lower() == 'done':
            break
        if not voter.isdigit():
            print("⚠️ Please enter a numeric voter ID.")
            continue
        vote = input("Enter vote choice: ").strip()
        tree.cast_vote(int(voter), vote)

    tree.summarize()
    print("\n✅ Voting session completed.")

if __name__ == "__main__":
    run_cli()
