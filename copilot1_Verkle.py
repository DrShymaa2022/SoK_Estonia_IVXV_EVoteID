//Copilot Python Simulation
import hashlib
import secrets
import asyncio
from sympy import symbols, interpolate
from py_ecc.optimized_bls12_381 import curve_order, G1, multiply, add, Z1

# ----- Trusted Setup -----
def trusted_setup(degree):
    r = secrets.randbelow(curve_order - 2) + 2
    powers = [multiply(G1, pow(r, i, curve_order)) for i in range(degree + 1)]
    return powers

# ----- Hash Vote -----
def hash_vote(vote_data):
    h = hashlib.sha256(vote_data.encode()).hexdigest()
    return int(h, 16) % curve_order

# ----- Polynomial Commitment -----
def commit_polynomial(coeffs, setup):
    commitment = Z1
    for i, coeff in enumerate(coeffs):
        commitment = add(commitment, multiply(setup[i], coeff))
    return commitment

# ----- Verkle Tree Manager -----
class VerkleManager:
    def __init__(self, max_votes=100):
        self.setup = trusted_setup(max_votes)
        self.votes_all = []      # VT₁
        self.votes_final = {}    # VT₂
        self.votes_multiple = {} # VT₃
        self.commitments = {}
        self.proof_queue = []

    def insert_vote(self, voter_id, vote_data):
        vote_hash = hash_vote(vote_data)
        self.votes_all.append((voter_id, vote_hash))
        self.proof_queue.append((voter_id, vote_hash))

        if voter_id in self.votes_final:
            # Move old vote to VT₃
            self.votes_multiple.setdefault(voter_id, []).append(self.votes_final[voter_id])
        self.votes_final[voter_id] = vote_hash

        print(f"✅ Voter {voter_id} voted: {vote_data} → Hash {vote_hash}")

    def generate_commitments(self):
        x = symbols('x')

        def interpolate_votes(vote_list):
            points = [(i, vote_hash) for i, (_, vote_hash) in enumerate(vote_list)]
            poly = interpolate(points, x)
            coeffs = [int(c) % curve_order for c in poly.all_coeffs()]
            return commit_polynomial(coeffs, self.setup)

        # VT₁: All votes
        self.commitments['VT1'] = interpolate_votes(self.votes_all)

        # VT₂: Final votes
        final_list = list(self.votes_final.items())
        self.commitments['VT2'] = interpolate_votes(final_list)

        # VT₃: Multiple votes
        multi_list = [(voter, h) for voter, hashes in self.votes_multiple.items() for h in hashes]
        self.commitments['VT3'] = interpolate_votes(multi_list)

        print("📌 Commitments generated for VT₁, VT₂, VT₃.")

    def verify_vote_inclusion(self, voter_id, vote_hash, tree='VT2'):
        # Simulated verification: check if vote_hash is in the polynomial interpolation
        if tree == 'VT1':
            return any(vh == vote_hash for _, vh in self.votes_all)
        elif tree == 'VT2':
            return self.votes_final.get(voter_id) == vote_hash
        elif tree == 'VT3':
            return vote_hash in self.votes_multiple.get(voter_id, [])
        return False

    async def background_proof_generator(self):
        while True:
            if self.proof_queue:
                batch = self.proof_queue[:10]
                del self.proof_queue[:10]
                await asyncio.sleep(0.5)
                print(f"🔄 Generating batch proof for {len(batch)} votes...")
                for voter_id, vote_hash in batch:
                    included = self.verify_vote_inclusion(voter_id, vote_hash, tree='VT2')
                    print(f"🧾 Proof for Voter {voter_id}: {'✅ Verified' if included else '❌ Not found'}")
            else:
                await asyncio.sleep(1)

# ----- Main Simulation -----
async def main():
    vm = VerkleManager(max_votes=100)
    asyncio.create_task(vm.background_proof_generator())

    for voter_id in range(20):
        vote = f"choice_{secrets.randbelow(5) + 1}"
        vm.insert_vote(voter_id, vote)
        await asyncio.sleep(0.2)

    vm.generate_commitments()
    print("✅ All commitments ready. Background proof generation continues...")

asyncio.run(main())
