
from proxysrv.data.database import DBBase
from proxysrv.data.models import (
    PCBIDCollection,
    XMLRewriteRule,
    XMLRewriteNode,
)

class XMLRewriteData:
    @staticmethod
    def _serialize_node(node: XMLRewriteNode) -> dict:
        return {
            "id": node.id,
            "parent_id": node.parent_id,
            "position": node.position,
            "key": node.key,
            "value": node.value,
            "operation": node.operation,
            "replacement_key": node.replacement_key,
            "replacement_value": node.replacement_value,
            "options": node.options,
            "enabled": node.enabled,
            "children": [
                XMLRewriteData._serialize_node(child)
                for child in node.children
            ],
        }

    @staticmethod
    def _serialize_rule(rule: XMLRewriteRule) -> dict:
        return {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "enabled": rule.enabled,
            "priority": rule.priority,
            "collection_id": rule.collection_id,
            "created_at": rule.created_at,
            "updated_at": rule.updated_at,
            "nodes": [
                XMLRewriteData._serialize_node(node)
                for node in rule.nodes
                if node.parent_id is None
            ],
        }

    @staticmethod
    def get_rule(rule_id: int) -> dict | None:
        with DBBase.SessionLocal() as session:
            rule = session.query(XMLRewriteRule).filter(
                XMLRewriteRule.id == rule_id
            ).first()

            if rule is None:
                return None

            return XMLRewriteData._serialize_rule(rule)

    @staticmethod
    def list_rules(
        enabled: bool | None = None,
        collection_id: int | None = None,
    ) -> list[dict]:
        with DBBase.SessionLocal() as session:
            query = session.query(XMLRewriteRule)

            if enabled is not None:
                query = query.filter(
                    XMLRewriteRule.enabled == enabled
                )

            if collection_id is not None:
                query = query.filter(
                    XMLRewriteRule.collection_id == collection_id
                )

            rules = query.order_by(
                XMLRewriteRule.priority,
                XMLRewriteRule.id,
            ).all()

            return [
                XMLRewriteData._serialize_rule(rule)
                for rule in rules
            ]

    @staticmethod
    def get_applicable_rules(
        collection_id: int | None = None,
    ) -> list[dict]:
        """Return global rules and rules for the specified collection."""
        with DBBase.SessionLocal() as session:
            query = session.query(XMLRewriteRule).filter(
                XMLRewriteRule.enabled.is_(True)
            )

            if collection_id is None:
                query = query.filter(
                    XMLRewriteRule.collection_id.is_(None)
                )
            else:
                query = query.filter(
                    (XMLRewriteRule.collection_id.is_(None))
                    | (XMLRewriteRule.collection_id == collection_id)
                )

            rules = query.order_by(
                XMLRewriteRule.priority,
                XMLRewriteRule.id,
            ).all()

            return [
                XMLRewriteData._serialize_rule(rule)
                for rule in rules
            ]

    @staticmethod
    def create_rule(
        name: str,
        description: str | None = None,
        priority: int = 100,
        collection_id: int | None = None,
        enabled: bool = True,
    ) -> dict:
        with DBBase.SessionLocal() as session:
            if collection_id is not None:
                collection = session.query(
                    PCBIDCollection
                ).filter(
                    PCBIDCollection.id == collection_id
                ).first()

                if collection is None:
                    raise ValueError("Collection does not exist")

            rule = XMLRewriteRule(
                name=name,
                description=description,
                priority=priority,
                collection_id=collection_id,
                enabled=enabled,
            )

            session.add(rule)
            session.flush()

            result = XMLRewriteData._serialize_rule(rule)
            session.commit()

            return result

    @staticmethod
    def set_enabled(
        rule_id: int,
        enabled: bool,
    ) -> dict | None:
        with DBBase.SessionLocal() as session:
            rule = session.query(XMLRewriteRule).filter(
                XMLRewriteRule.id == rule_id
            ).first()

            if rule is None:
                return None

            rule.enabled = enabled
            session.flush()

            result = XMLRewriteData._serialize_rule(rule)
            session.commit()

            return result

    @staticmethod
    def delete_rule(rule_id: int) -> bool:
        with DBBase.SessionLocal() as session:
            rule = session.query(XMLRewriteRule).filter(
                XMLRewriteRule.id == rule_id
            ).first()

            if rule is None:
                return False

            session.delete(rule)
            session.commit()

            return True

    @staticmethod
    def add_node(
        rule_id: int,
        key: str,
        parent_id: int | None = None,
        position: int = 0,
        value: str | None = None,
        operation: str = "replace",
        replacement_key: str | None = None,
        replacement_value: str | None = None,
        options: str | None = None,
        enabled: bool = True,
    ) -> dict:
        with DBBase.SessionLocal() as session:
            rule = session.query(XMLRewriteRule).filter(
                XMLRewriteRule.id == rule_id
            ).first()

            if rule is None:
                raise ValueError("Rewrite rule does not exist")

            if parent_id is not None:
                parent = session.query(XMLRewriteNode).filter(
                    XMLRewriteNode.id == parent_id,
                    XMLRewriteNode.rule_id == rule_id,
                ).first()

                if parent is None:
                    raise ValueError(
                        "Parent node does not belong to this rule"
                    )

            node = XMLRewriteNode(
                rule_id=rule_id,
                parent_id=parent_id,
                position=position,
                key=key,
                value=value,
                operation=operation,
                replacement_key=replacement_key,
                replacement_value=replacement_value,
                options=options,
                enabled=enabled,
            )

            session.add(node)
            session.flush()

            result = XMLRewriteData._serialize_node(node)
            session.commit()

            return result

    @staticmethod
    def delete_node(node_id: int) -> bool:
        with DBBase.SessionLocal() as session:
            node = session.query(XMLRewriteNode).filter(
                XMLRewriteNode.id == node_id
            ).first()

            if node is None:
                return False

            session.delete(node)
            session.commit()

            return True
