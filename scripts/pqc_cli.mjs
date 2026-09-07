#!/usr/bin/env node
/**
 * Martin's Algorithm // PQC CLI Bridge
 * Exposes NIST FIPS 203 ML-KEM-768 and NIST FIPS 204 ML-DSA-65 to Python & CLI
 */

import { ml_kem768 } from '@noble/post-quantum/ml-kem.js';
import { ml_dsa65 } from '@noble/post-quantum/ml-dsa.js';
import { sha256 } from '@noble/hashes/sha256';
import { hkdf } from '@noble/hashes/hkdf';

const action = process.argv[2];

function hexToBytes(hex) {
  const clean = hex.replace(/[^0-9a-fA-F]/g, '');
  const bytes = new Uint8Array(clean.length / 2);
  for (let i = 0; i < clean.length; i += 2) {
    bytes[i / 2] = parseInt(clean.substring(i, i + 2), 16);
  }
  return bytes;
}

function bytesToHex(bytes) {
  return Buffer.from(bytes).toString('hex');
}

try {
  if (action === 'keygen_dsa') {
    const seed = process.argv[3] ? hexToBytes(process.argv[3]) : undefined;
    const pair = seed ? ml_dsa65.keygen(seed.slice(0, 32)) : ml_dsa65.keygen();
    console.log(JSON.stringify({
      publicKeyHex: bytesToHex(pair.publicKey),
      secretKeyHex: bytesToHex(pair.secretKey)
    }));
  } else if (action === 'sign_dsa') {
    const message = Buffer.from(process.argv[3], 'utf8');
    const secretKey = hexToBytes(process.argv[4]);
    const sig = ml_dsa65.sign(message, secretKey);
    console.log(JSON.stringify({
      signatureHex: bytesToHex(sig)
    }));
  } else if (action === 'verify_dsa') {
    const signature = hexToBytes(process.argv[3]);
    const message = Buffer.from(process.argv[4], 'utf8');
    const publicKey = hexToBytes(process.argv[5]);
    const valid = ml_dsa65.verify(signature, message, publicKey);
    console.log(JSON.stringify({ valid }));
  } else if (action === 'keygen_kem') {
    const seed = process.argv[3] ? hexToBytes(process.argv[3]) : undefined;
    const pair = seed ? ml_kem768.keygen(seed.slice(0, 64)) : ml_kem768.keygen();
    console.log(JSON.stringify({
      publicKeyHex: bytesToHex(pair.publicKey),
      secretKeyHex: bytesToHex(pair.secretKey)
    }));
  } else if (action === 'encaps_kem') {
    const publicKey = hexToBytes(process.argv[3]);
    const res = ml_kem768.encapsulate(publicKey);
    console.log(JSON.stringify({
      ciphertextHex: bytesToHex(res.cipherText),
      sharedSecretHex: bytesToHex(res.sharedSecret)
    }));
  } else if (action === 'decaps_kem') {
    const ciphertext = hexToBytes(process.argv[3]);
    const secretKey = hexToBytes(process.argv[4]);
    const sharedSecret = ml_kem768.decapsulate(ciphertext, secretKey);
    console.log(JSON.stringify({
      sharedSecretHex: bytesToHex(sharedSecret)
    }));
  } else {
    console.error(JSON.stringify({ error: `Unknown action: ${action}` }));
    process.exit(1);
  }
} catch (err) {
  console.error(JSON.stringify({ error: err.message }));
  process.exit(1);
}
