class Parser:

    FORM_TITLE = 1
    SECTION_TITLE = 2
    FIELD_LABEL = 3
    FIELD_SPACE = 4
    NOTE = 5


    def __call__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

        accepted = self._parseDocument()

        # must consume everything
        if self._current() is not None:
            self.errors.append("Extra tokens after document end")
            accepted = False

        return accepted and len(self.errors) == 0, self.errors

    # Utilities

    def _current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _advance(self):
        self.pos += 1

    def _match(self, expected):
        tok = self._current()
        if tok and tok.id == expected:
            self._advance()
            return True

        self.errors.append(
            f"Expected token {expected}, got {tok.id if tok else 'EOF'}"
        )
        self._panicRecovery()
        return False

    # Panic Recovery

    def _panicRecovery(self):
        """
        Skip tokens until a synchronizing token
        """
        sync_tokens = {Parser.SECTION_TITLE, Parser.FIELD_LABEL, Parser.NOTE}

        while self._current() is not None and self._current().id not in sync_tokens:
            self._advance()

    # Grammar

    # DOCUMENT → FORM_TITLE SECTION_LIST
    def _parseDocument(self):
        ok = True
        ok &= self._parseFormTitle()
        ok &= self._parseSectionList()
        return ok

    # FORM_TITLE
    def _parseFormTitle(self):
        return self._match(Parser.FORM_TITLE)

    # SECTION_LIST → SECTION*
    def _parseSectionList(self):
        ok = True
        while self._current() and self._current().id in (
            Parser.SECTION_TITLE,
            Parser.FIELD_LABEL,
            Parser.NOTE,
        ):
            ok &= self._parseSection()
        return ok

    # SECTION → SECTION_TITLE SECTION_BODY | SECTION_BODY
    def _parseSection(self):
        ok = True
        if self._current().id == Parser.SECTION_TITLE:
            ok &= self._match(Parser.SECTION_TITLE)
        ok &= self._parseSectionBody()
        return ok

    # SECTION_BODY → FORM_ELEMENT_LIST
    def _parseSectionBody(self):
        return self._parseFormElementList()

    # FORM_ELEMENT_LIST → FORM_ELEMENT*
    def _parseFormElementList(self):
        ok = True
        while self._current() and self._current().id in (Parser.FIELD_LABEL, Parser.NOTE):
            ok &= self._parseFormElement()
        return ok

    # FORM_ELEMENT → FIELD | NOTE
    def _parseFormElement(self):
        if self._current().id == Parser.FIELD_LABEL:
            return self._parseField()
        elif self._current().id == Parser.NOTE:
            return self._match(Parser.NOTE)

        self.errors.append(
            f"Invalid form element: {self._current().id}"
        )
        self._panicRecovery()
        return False

    # FIELD → FIELD_LABEL FIELD_SPACE
    def _parseField(self):
        ok = True
        ok &= self._match(Parser.FIELD_LABEL)
        ok &= self._match(Parser.FIELD_SPACE)
        return ok
