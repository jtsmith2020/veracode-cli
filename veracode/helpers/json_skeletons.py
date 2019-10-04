


class JSONSkeleton:

    file = """[  
  {
    branch_match: ".*",
    description: ""
    app_id: "",
  }
]"""

    static = """    static: {
      type: "policy",
      naming: "",
      upload: [
        "target/verademo.war",
        "target/another.war"
      ],
      modules: [
        "verademo.war"
      ]
    }"""