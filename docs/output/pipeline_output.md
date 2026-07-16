# CT-200 Pipeline — Full End-to-End Run Output
Captured: 2026-07-16T10:49:53.604224+00:00

This file was generated automatically by `app/services/capture_pipeline_output.py`, running the real versioning + staleness flow against a live server — not hand-edited.

## 0. Server health check
```
GET / -> 200
{
  "status": "ok"
}
```

## 1. Ingest v1
```
Ingested 'v1' as DocumentVersion id=4
```

## 2. Browse v1 sections
```
GET /browse/sections?version=v1 -> 200
[
  {
    "heading_number": "1",
    "heading_text": "Device Overview",
    "level": 1,
    "body_text": "The CardioTrack CT-200 is an oscillometric, upper-arm blood pressure\nmonitor intended for home use by adult users. It measures systolic\npressure, diastolic pressure, and pulse rate, and stores up to 200\nreadings across two user pro\ufb01les.",
    "content_hash": "55ca481183039ea25c929c4c01b158f7db6d427a88d40746faf7e050fc8a38f3",
    "order_index": 3,
    "id": 2,
    "document_version_id": 1,
    "parent_id": 1
  },
  {
    "heading_number": "2",
    "heading_text": "Physical and Electrical Speci\ufb01cations",
    "level": 1,
    "body_text": "",
    "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "order_index": 19,
    "id": 5,
    "document_version_id": 1,
    "parent_id": 1
  },
  {
    "heading_number": "3",
    "heading_text": "Device Operation",
    "level": 1,
    "body_text": "",
    "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "order_index": 53,
    "id": 9,
    "document_version_id": 1,
    "parent_id": 1
  },
  {
    "heading_number": "4",
    "heading_text": "Alarms and Safety Behavior",
    "level": 1,
    "body_text": "",
    "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "order_index": 83,
    "id": 14,
    "document_version_id": 1,
    "parent_id": 1
  },
  {
    "heading_number": "5",
    "heading_text": "Data Management",
    "level": 1,
    "body_text": "",
    "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "order_index": 122,
    "id": 18,
    "document_version_id": 1,
    "parent_id": 1
  },
  {
    "heading_number": "6",
    "heading_text": "Maintenance and Cleaning",
    "level": 1,
    "body_text": "",
    "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "order_index": 139,
    "id": 21,
    "document_version_id": 1,
    "parent_id": 1
  },
  {
    "heading_number": "7",
    "heading_text": "Troubleshooting",
    "level": 1,
    "body_text": "",
    "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "order_index": 151,
    "id": 24,
    "document_version_id": 1,
    "parent_id": 1
  },
  {
    "heading_number": "8",
    "heading_text": "Regulatory Information",
    "level": 1,
    "body_text": "",
    "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "order_index": 166,
    "id": 27,
    "document_version_id": 1,
    "parent_id": 1
  }
]
```

## 2b. Search for 'battery' in v1
```
GET /browse/search?q=battery&version=v1 -> 200
[
  {
    "heading_number": "2.1.1.1",
    "heading_text": "Battery Life Under Typical Use",
    "level": 4,
    "body_text": "Under typical use (three measurements per day), four AA alkaline\nbatteries provide approximately 300 measurement cycles before\nrequiring replacement. The device displays a low\n\u2011\nbattery icon once\nremaining capacity falls below 15%.",
    "content_hash": "95ff8f7484dac8e3fb51fee151c481c96b6034f0bb12e0b5a0d72d76788045f3",
    "order_index": 37,
    "id": 7,
    "document_version_id": 1,
    "parent_id": 6
  },
  {
    "heading_number": "3.4",
    "heading_text": "Auto Shuto\ufb00",
    "level": 2,
    "body_text": "To conserve battery, the CT\n\u2011\n200 automatically powers o\ufb00 after 60\nseconds of inactivity on the home screen, and after 3 minutes of\ninactivity if a measurement screen is left open without starting a reading.",
    "content_hash": "8d0900b3fc3d73ca7e23695f281c2700112011f0f27f00fb8a484de6a49c9af8",
    "order_index": 65,
    "id": 12,
    "document_version_id": 1,
    "parent_id": 9
  },
  {
    "heading_number": "4.2",
    "heading_text": "Error Codes",
    "level": 2,
    "body_text": "Code\nMeaning\nDevice Behavior\nE1\nCu\ufb00 not connected or\nleak detected\nAborts measurement, displays E1\nE2\nMotion artifact detected\nduring measurement\nAborts measurement, displays\nE2, prompts retry\nE3\nOverpressure condition\nAuto-de\ufb02ates within 2 seconds,\ndisplays E3\nE4\nLow battery during\nmeasurement\nAborts measurement, displays E4\nE5\nInternal sensor fault\nDevice disables measurement\nfunction, displays E5 until\nserviced",
    "content_hash": "a308eae7a63c06b9b6b0dc5fc04b7a4f35fca1a7d1b7802588ab9d0f066946cc",
    "order_index": 89,
    "id": 16,
    "document_version_id": 1,
    "parent_id": 14
  }
]
```

## 2c. Resolved battery node id
```
7
```

## 3. Create selection
```
POST /selections -> 200
{
  "id": 2,
  "name": "battery-and-alarms",
  "created_at": "2026-07-16T10:49:49",
  "items": [
    {
      "node_id": 7,
      "document_version_id": 1,
      "heading_text": "Battery Life Under Typical Use",
      "heading_number": "2.1.1.1",
      "body_text": "Under typical use (three measurements per day), four AA alkaline\nbatteries provide approximately 300 measurement cycles before\nrequiring replacement. The device displays a low\n\u2011\nbattery icon once\nremaining capacity falls below 15%."
    }
  ]
}
```

## 4. Generate test cases
```
POST /generations/selections/2 -> 200
{
  "status": "generated",
  "generation_id": 2,
  "selection_id": 2,
  "generated_at": "2026-07-16T10:49:52.682076+00:00",
  "source_nodes": [
    {
      "node_id": 7,
      "content_hash": "95ff8f7484dac8e3fb51fee151c481c96b6034f0bb12e0b5a0d72d76788045f3"
    }
  ],
  "test_cases": [
    {
      "id": "TC-1",
      "title": "Low Battery Icon Display",
      "steps": [
        "Set the device to measure blood pressure three times a day.",
        "Wait until the device displays a low battery icon.",
        "Verify the icon is displayed correctly."
      ],
      "expected_result": "The low battery icon is displayed once the remaining capacity falls below 15%."
    },
    {
      "id": "TC-2",
      "title": "Battery Life Under Typical Use",
      "steps": [
        "Set the device to measure blood pressure three times a day.",
        "Monitor the device's battery life until it reaches 15% capacity.",
        "Verify the device has approximately 300 measurement cycles before requiring battery replacement."
      ],
      "expected_result": "The device has approximately 300 measurement cycles before requiring battery replacement."
    },
    {
      "id": "TC-3",
      "title": "Battery Life Calculation",
      "steps": [
        "Set the device to measure blood pressure three times a day.",
        "Calculate the number of measurement cycles after 15% battery capacity is reached.",
        "Verify the calculated value is close to 300 measurement cycles."
      ],
      "expected_result": "The calculated value is close to 300 measurement cycles."
    }
  ]
}
```

## 5. Check staleness (before v2 — expect is_stale=false)
```
GET /generations?selection_id=2 -> 200
[
  {
    "generation_id": 2,
    "selection_id": 2,
    "generated_at": "2026-07-16T10:49:52.682076+00:00",
    "source_nodes": [
      {
        "node_id": 7,
        "content_hash": "95ff8f7484dac8e3fb51fee151c481c96b6034f0bb12e0b5a0d72d76788045f3"
      }
    ],
    "test_cases": [
      {
        "id": "TC-1",
        "title": "Low Battery Icon Display",
        "steps": [
          "Set the device to measure blood pressure three times a day.",
          "Wait until the device displays a low battery icon.",
          "Verify the icon is displayed correctly."
        ],
        "expected_result": "The low battery icon is displayed once the remaining capacity falls below 15%."
      },
      {
        "id": "TC-2",
        "title": "Battery Life Under Typical Use",
        "steps": [
          "Set the device to measure blood pressure three times a day.",
          "Monitor the device's battery life until it reaches 15% capacity.",
          "Verify the device has approximately 300 measurement cycles before requiring battery replacement."
        ],
        "expected_result": "The device has approximately 300 measurement cycles before requiring battery replacement."
      },
      {
        "id": "TC-3",
        "title": "Battery Life Calculation",
        "steps": [
          "Set the device to measure blood pressure three times a day.",
          "Calculate the number of measurement cycles after 15% battery capacity is reached.",
          "Verify the calculated value is close to 300 measurement cycles."
        ],
        "expected_result": "The calculated value is close to 300 measurement cycles."
      }
    ],
    "staleness": {
      "generation_id": 2,
      "is_stale": false,
      "stale_nodes": []
    }
  }
]
```

## 6. Ingest v2
```
Ingested 'v2' as DocumentVersion id=5
```

## 7. Check staleness (after v2 — expect is_stale=true)
```
GET /generations?selection_id=2 -> 200
[
  {
    "generation_id": 2,
    "selection_id": 2,
    "generated_at": "2026-07-16T10:49:52.682076+00:00",
    "source_nodes": [
      {
        "node_id": 7,
        "content_hash": "95ff8f7484dac8e3fb51fee151c481c96b6034f0bb12e0b5a0d72d76788045f3"
      }
    ],
    "test_cases": [
      {
        "id": "TC-1",
        "title": "Low Battery Icon Display",
        "steps": [
          "Set the device to measure blood pressure three times a day.",
          "Wait until the device displays a low battery icon.",
          "Verify the icon is displayed correctly."
        ],
        "expected_result": "The low battery icon is displayed once the remaining capacity falls below 15%."
      },
      {
        "id": "TC-2",
        "title": "Battery Life Under Typical Use",
        "steps": [
          "Set the device to measure blood pressure three times a day.",
          "Monitor the device's battery life until it reaches 15% capacity.",
          "Verify the device has approximately 300 measurement cycles before requiring battery replacement."
        ],
        "expected_result": "The device has approximately 300 measurement cycles before requiring battery replacement."
      },
      {
        "id": "TC-3",
        "title": "Battery Life Calculation",
        "steps": [
          "Set the device to measure blood pressure three times a day.",
          "Calculate the number of measurement cycles after 15% battery capacity is reached.",
          "Verify the calculated value is close to 300 measurement cycles."
        ],
        "expected_result": "The calculated value is close to 300 measurement cycles."
      }
    ],
    "staleness": {
      "generation_id": 2,
      "is_stale": true,
      "stale_nodes": [
        {
          "node_id": 7,
          "reason": "content_changed"
        }
      ]
    }
  }
]
```

## 8. Original selection still resolves to exact pinned v1 text
```
GET /selections/2 -> 200
{
  "id": 2,
  "name": "battery-and-alarms",
  "created_at": "2026-07-16T10:49:49",
  "items": [
    {
      "node_id": 7,
      "document_version_id": 1,
      "heading_text": "Battery Life Under Typical Use",
      "heading_number": "2.1.1.1",
      "body_text": "Under typical use (three measurements per day), four AA alkaline\nbatteries provide approximately 300 measurement cycles before\nrequiring replacement. The device displays a low\n\u2011\nbattery icon once\nremaining capacity falls below 15%."
    }
  ]
}
```
