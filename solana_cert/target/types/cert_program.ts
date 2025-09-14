/**
 * Program IDL in camelCase format in order to be used in JS/TS.
 *
 * Note that this is only a type helper and is not the actual IDL. The original
 * IDL can be found at `target/idl/cert_program.json`.
 */
export type CertProgram = {
  "address": "GAngKGB1TtogbjxV6nMac26mSS7EexguQmct1fQkLdUB",
  "metadata": {
    "name": "certProgram",
    "version": "0.1.0",
    "spec": "0.1.0",
    "description": "Created with Anchor"
  },
  "instructions": [
    {
      "name": "issueCertificate",
      "discriminator": [
        61,
        197,
        55,
        28,
        159,
        18,
        132,
        128
      ],
      "accounts": [
        {
          "name": "certificateAccount",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  99,
                  101,
                  114,
                  116,
                  105,
                  102,
                  105,
                  99,
                  97,
                  116,
                  101
                ]
              },
              {
                "kind": "arg",
                "path": "certId"
              }
            ]
          }
        },
        {
          "name": "issuer",
          "writable": true,
          "signer": true
        },
        {
          "name": "systemProgram",
          "address": "11111111111111111111111111111111"
        }
      ],
      "args": [
        {
          "name": "certId",
          "type": "string"
        },
        {
          "name": "dataHash",
          "type": "string"
        },
        {
          "name": "encryptedCid",
          "type": "string"
        },
        {
          "name": "metadataIpfsCid",
          "type": "string"
        },
        {
          "name": "serialNumber",
          "type": "u64"
        }
      ]
    },
    {
      "name": "revokeCertificate",
      "discriminator": [
        236,
        5,
        130,
        119,
        9,
        164,
        130,
        122
      ],
      "accounts": [
        {
          "name": "certificateAccount",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  99,
                  101,
                  114,
                  116,
                  105,
                  102,
                  105,
                  99,
                  97,
                  116,
                  101
                ]
              },
              {
                "kind": "arg",
                "path": "certId"
              }
            ]
          }
        },
        {
          "name": "issuer",
          "signer": true
        }
      ],
      "args": [
        {
          "name": "certId",
          "type": "string"
        }
      ]
    },
    {
      "name": "verifyCertificate",
      "discriminator": [
        85,
        168,
        68,
        192,
        185,
        249,
        46,
        99
      ],
      "accounts": [
        {
          "name": "certificateAccount",
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  99,
                  101,
                  114,
                  116,
                  105,
                  102,
                  105,
                  99,
                  97,
                  116,
                  101
                ]
              },
              {
                "kind": "arg",
                "path": "certId"
              }
            ]
          }
        }
      ],
      "args": [
        {
          "name": "certId",
          "type": "string"
        },
        {
          "name": "dataHash",
          "type": "string"
        }
      ]
    }
  ],
  "accounts": [
    {
      "name": "certificate",
      "discriminator": [
        202,
        229,
        222,
        220,
        116,
        20,
        74,
        67
      ]
    }
  ],
  "events": [
    {
      "name": "certificateIssued",
      "discriminator": [
        62,
        59,
        26,
        207,
        181,
        234,
        201,
        52
      ]
    },
    {
      "name": "certificateRevoked",
      "discriminator": [
        99,
        180,
        224,
        20,
        200,
        221,
        133,
        47
      ]
    }
  ],
  "errors": [
    {
      "code": 6000,
      "name": "unauthorizedIssuer",
      "msg": "You are not authorized to perform this action."
    },
    {
      "code": 6001,
      "name": "hashMismatch",
      "msg": "The provided hash does not match the stored hash."
    },
    {
      "code": 6002,
      "name": "certificateRevoked",
      "msg": "This certificate has been revoked."
    }
  ],
  "types": [
    {
      "name": "certificate",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "certId",
            "type": "string"
          },
          {
            "name": "issuer",
            "type": "pubkey"
          },
          {
            "name": "dataHash",
            "type": "string"
          },
          {
            "name": "encryptedCid",
            "type": "string"
          },
          {
            "name": "metadataIpfsCid",
            "type": "string"
          },
          {
            "name": "status",
            "type": {
              "defined": {
                "name": "certificateStatus"
              }
            }
          },
          {
            "name": "issuedAt",
            "type": "i64"
          },
          {
            "name": "serialNumber",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "certificateIssued",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "certId",
            "type": "string"
          },
          {
            "name": "issuer",
            "type": "pubkey"
          },
          {
            "name": "serialNumber",
            "type": "u64"
          }
        ]
      }
    },
    {
      "name": "certificateRevoked",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "certId",
            "type": "string"
          },
          {
            "name": "issuer",
            "type": "pubkey"
          }
        ]
      }
    },
    {
      "name": "certificateStatus",
      "type": {
        "kind": "enum",
        "variants": [
          {
            "name": "issued"
          },
          {
            "name": "revoked"
          }
        ]
      }
    }
  ]
};
