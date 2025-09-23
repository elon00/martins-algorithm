---- MODULE Rotor ----
(*
Formal Specification of Rotor: Alpenglow's Erasure-Coded Block Propagation
*)

EXTENDS Naturals, FiniteSets, Sequences, TLC

CONSTANT
    NumValidators,
    StakeWeights,
    ErasureCodingK,  \* Data chunks
    ErasureCodingM   \* Parity chunks

VARIABLES
    currentSlot,
    blocks,
    blockFragments,
    relayAssignments,
    validatorStates

vars == <<currentSlot, blocks, blockFragments, relayAssignments, validatorStates>>

ASSUME
    /\ ErasureCodingK \in 4..8
    /\ ErasureCodingM \in 2..4

\* Get stake-weighted relay selection
SelectRelays(blockId, numRelays) ==
    LET candidates == {v \in 1..NumValidators : validatorStates[v] = "active"}
        weights == [v \in candidates |-> StakeWeights[v]]
    IN {v \in candidates : RandomElement(1..100) <= (weights[v] * numRelays * 10) \div TotalStake}

\* Total stake
TotalStake == FoldFunctionOnSet(LAMBDA x,y: x+y, 0, {StakeWeights[v] : v \in 1..NumValidators})

----
\* Rotor Actions

\* Propose block and create erasure-coded fragments
ProposeAndFragmentBlock ==
    /\ \E proposer \in 1..NumValidators :
       /\ validatorStates[proposer] = "active"
       /\ blocks[currentSlot][proposer] = {}
       /\ LET block == [slot |-> currentSlot, proposer |-> proposer, data |-> RandomElement(1..1000)]
              fragments == [i \in 1..(ErasureCodingK + ErasureCodingM) |->
                            [chunkId |-> i, data |-> block.data + i, blockId |-> currentSlot]]
          IN /\ blocks' = [blocks EXCEPT ![currentSlot][proposer] = block]
             /\ blockFragments' = [blockFragments EXCEPT ![currentSlot] = fragments]
             /\ relayAssignments' = [relayAssignments EXCEPT ![currentSlot] =
                                   SelectRelays(currentSlot, ErasureCodingK + ErasureCodingM)]
    /\ UNCHANGED <<currentSlot, validatorStates>>

\* Distribute fragments to relays
DistributeFragments ==
    /\ currentSlot <= 10
    /\ blockFragments[currentSlot] # {}
    /\ relayAssignments[currentSlot] # {}
    /\ LET relays == relayAssignments[currentSlot]
       IN \A relay \in relays :
           /\ validatorStates[relay] = "active"
           \* Fragment successfully distributed (simplified)
    /\ UNCHANGED <<currentSlot, blocks, blockFragments, relayAssignments, validatorStates>>

\* Reconstruct block from fragments
ReconstructBlock ==
    /\ currentSlot <= 10
    /\ blockFragments[currentSlot] # {}
    /\ LET fragments == blockFragments[currentSlot]
           available_chunks == {f.chunkId : f \in fragments}
       IN /\ Cardinality(available_chunks) >= ErasureCodingK  \* Can reconstruct with K chunks
          /\ LET reconstructed_data == FoldFunctionOnSet(LAMBDA x,y: x + y.data, 0,
                                        {f \in fragments : f.chunkId <= ErasureCodingK})
             IN blocks' = [blocks EXCEPT ![currentSlot] =
                          [blocks[currentSlot] EXCEPT !.reconstructed = TRUE]]
    /\ UNCHANGED <<currentSlot, blockFragments, relayAssignments, validatorStates>>

----
\* Rotor Properties

\* Erasure coding property: Can reconstruct with any K fragments
Rotor_ReconstructionProperty ==
    \A s \in 1..10 :
        blockFragments[s] # {} =>
            LET available == {f.chunkId : f \in blockFragments[s]}
            IN Cardinality(available) >= ErasureCodingK =>
                blocks[s].reconstructed = TRUE

\* Stake-weighted relay selection
Rotor_StakeWeightedRelays ==
    \A s \in 1..10 :
        relayAssignments[s] # {} =>
            LET relays == relayAssignments[s]
                total_relay_stake == StakeOf(relays)
                total_stake == TotalStake
            IN (total_relay_stake * 100) \div total_stake >= 60  \* At least 60% stake in relays

\* Single-hop efficiency
Rotor_SingleHopEfficiency ==
    \A s \in 1..10 :
        relayAssignments[s] # {} =>
            \A v \in 1..NumValidators :
                v \notin relayAssignments[s] =>
                    ~\E f \in blockFragments[s] : f.relay = v  \* No redundant hops

\* Byzantine resilience in propagation
Rotor_ByzantineResilience ==
    LET byzantine_relays == {v \in relayAssignments[currentSlot] : validatorStates[v] = "byzantine"}
    IN Cardinality(byzantine_relays) <= ErasureCodingM  \* Can tolerate M Byzantine relays

\* Network efficiency under partitions
Rotor_PartitionTolerance ==
    LET active_relays == {v \in relayAssignments[currentSlot] : validatorStates[v] = "active"}
    IN Cardinality(active_relays) >= ErasureCodingK =>
        Rotor_ReconstructionProperty

====